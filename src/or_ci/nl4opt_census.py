from __future__ import annotations

import csv
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from or_ci.benchmark_answers import (
    NL4OPT_ANSWER_POLICY,
    answer_relation,
    answers_equal,
    canonical_solver_status,
    result_matches_answer,
)
from or_ci.nl4opt_audit import (
    NL4OPTError,
    OWNER_DECISION_VALUES,
    OWNER_MATERIAL_VALUES,
    OWNER_MECHANISM_VALUES,
    load_official_targets,
    map_benchmark_rows,
    read_jsonl,
    sha256_file,
    sha256_text,
    write_json,
    write_jsonl,
)


APPROVED_ROW_COUNT = 245
APPROVED_TARGET_MATCH_COUNTS = {
    "match_both": 219,
    "match_corrected_only": 12,
    "match_historical_only": 2,
    "match_neither": 12,
}
APPROVED_ANSWER_RELATION_COUNTS = {
    "unchanged": 223,
    "semantic_difference": 18,
    "encoding_equivalent": 4,
}
APPROVED_DOMAIN_STABILITY_COUNTS = {"stable": 122, "ambiguous": 123}
APPROVED_CANDIDATE_COUNT = 26
APPROVED_JULY_CANDIDATE_REUSE_COUNT = 14
APPROVED_TERRA_DELTA_IDS = (
    "nl4opt-row-0017",
    "nl4opt-row-0033",
    "nl4opt-row-0037",
    "nl4opt-row-0042",
    "nl4opt-row-0044",
    "nl4opt-row-0072",
    "nl4opt-row-0139",
    "nl4opt-row-0156",
    "nl4opt-row-0177",
    "nl4opt-row-0193",
    "nl4opt-row-0199",
    "nl4opt-row-0240",
)
APPROVED_CONTROL_SEED = "nl4opt-full-census-v1"
APPROVED_STABLE_CONTROL_IDS = (
    "nl4opt-row-0068",
    "nl4opt-row-0061",
    "nl4opt-row-0010",
    "nl4opt-row-0192",
    "nl4opt-row-0065",
)
APPROVED_AMBIGUOUS_CONTROL_IDS = (
    "nl4opt-row-0055",
    "nl4opt-row-0207",
    "nl4opt-row-0026",
    "nl4opt-row-0245",
    "nl4opt-row-0184",
)
APPROVED_EVIDENCE_STATE_COUNTS = {
    "june_only": 176,
    "june_plus_july": 31,
    "july_only": 7,
    "none": 31,
}
FIXED_SOL_CONTROL_IDS = (
    "nl4opt-row-0068",
    "nl4opt-row-0061",
    "nl4opt-row-0055",
    "nl4opt-row-0207",
)
SOL_PRIORITY = (
    "source_target_conflict",
    "solver_status_conflict",
    "numeric_answer_conflict",
    "domain_ambiguity",
)
SOURCE_MANIFEST_FIELDS = {"row_id", "split", "statement_path", "source_sha256"}
TERMINAL_RUN_STATES = {
    "success",
    "artifact_invalid",
    "leakage_blocked",
    "model_failed",
    "solver_failed",
    "timed_out",
    "failed",
}


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise NL4OPTError(f"required JSON file is missing: {path}") from exc
    if not isinstance(payload, dict):
        raise NL4OPTError(f"expected JSON object: {path}")
    return payload


def _campaign_outputs_dir(path: Path) -> Path:
    if (path / "source").is_dir():
        return path.resolve()
    nested = path / "campaign_outputs"
    if (nested / "source").is_dir():
        return nested.resolve()
    raise NL4OPTError(f"campaign output directory lacks source/: {path}")


def _index_rows(rows: Iterable[dict[str, Any]], key: str, *, label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        value = str(row.get(key, "")).strip()
        if not value:
            raise NL4OPTError(f"{label} row is missing {key}")
        if value in indexed:
            raise NL4OPTError(f"duplicate {label} {key}: {value}")
        indexed[value] = row
    return indexed


def _normalized_question_sha256(question: str) -> str:
    return sha256_text(" ".join(question.split()))


def _source_text(question: Any) -> str:
    return str(question).rstrip() + "\n"


def _row_number(row_id: str) -> int:
    match = re.fullmatch(r"nl4opt-row-(\d{4})", row_id)
    if not match:
        raise NL4OPTError(f"invalid NL4OPT row ID: {row_id}")
    return int(match.group(1))


def _target_match(historical_matches: bool, corrected_matches: bool) -> str:
    if historical_matches and corrected_matches:
        return "match_both"
    if corrected_matches:
        return "match_corrected_only"
    if historical_matches:
        return "match_historical_only"
    return "match_neither"


def _domain_stability(result: dict[str, Any]) -> str:
    continuous = result.get("continuous", {})
    integer = result.get("integer", {})
    if not isinstance(continuous, dict) or not isinstance(integer, dict):
        return "ambiguous"
    statuses_equal = canonical_solver_status(continuous.get("status")) == canonical_solver_status(
        integer.get("status")
    )
    objectives_equal = answers_equal(
        continuous.get("objective"),
        integer.get("objective"),
        policy=NL4OPT_ANSWER_POLICY,
    )
    return "stable" if statuses_equal and objectives_equal else "ambiguous"


def classify_census_rows(
    *,
    historical_rows: list[dict[str, Any]],
    corrected_rows: list[dict[str, Any]],
    mappings: list[dict[str, Any]],
    solver_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Map official solver results to dataset rows and classify both interfaces."""
    if not (len(historical_rows) == len(corrected_rows) == len(mappings)):
        raise NL4OPTError("historical, corrected, and mapping row counts differ")
    solver_by_source = _index_rows(solver_rows, "source_id", label="official solver result")
    mapped_results: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    for index, (historical, corrected, mapping) in enumerate(
        zip(historical_rows, corrected_rows, mappings, strict=True)
    ):
        row_id = str(mapping["row_id"])
        source_id = str(mapping["source_id"])
        if source_id not in solver_by_source:
            raise NL4OPTError(f"{row_id}: no official solver result for source {source_id}")
        solver = solver_by_source[source_id]
        continuous = solver.get("continuous")
        integer = solver.get("integer")
        if not isinstance(continuous, dict) or not isinstance(integer, dict):
            raise NL4OPTError(f"{row_id}: official solver result lacks both domains")
        historical_answer = historical.get("en_answer")
        corrected_answer = corrected.get("en_answer")
        historical_by_domain = {
            domain: result_matches_answer(
                solver[domain], historical_answer, policy=NL4OPT_ANSWER_POLICY
            )
            for domain in ("continuous", "integer")
        }
        corrected_by_domain = {
            domain: result_matches_answer(
                solver[domain], corrected_answer, policy=NL4OPT_ANSWER_POLICY
            )
            for domain in ("continuous", "integer")
        }
        target_match = _target_match(
            any(historical_by_domain.values()), any(corrected_by_domain.values())
        )
        relation = answer_relation(
            historical_answer, corrected_answer, policy=NL4OPT_ANSWER_POLICY
        )
        stability = _domain_stability(solver)
        mapped_results.append(
            {
                "row_id": row_id,
                "source_id": source_id,
                "document_sha256": solver.get("document_sha256"),
                "continuous": continuous,
                "integer": integer,
            }
        )
        comparisons.append(
            {
                "row_id": row_id,
                "dataset_index_zero": index,
                "dataset_row_number": index + 1,
                "source_id": source_id,
                "dataset_question_sha256": _normalized_question_sha256(
                    str(historical.get("en_question", ""))
                ),
                "historical_answer": historical_answer,
                "corrected_answer": corrected_answer,
                "answer_relation": relation,
                "continuous_status": continuous.get("status"),
                "continuous_objective": continuous.get("objective"),
                "integer_status": integer.get("status"),
                "integer_objective": integer.get("objective"),
                "historical_matches_continuous": historical_by_domain["continuous"],
                "historical_matches_integer": historical_by_domain["integer"],
                "corrected_matches_continuous": corrected_by_domain["continuous"],
                "corrected_matches_integer": corrected_by_domain["integer"],
                "target_match": target_match,
                "candidate": target_match != "match_both",
                "domain_stability": stability,
                "domain_ambiguous": stability == "ambiguous",
                "formal_target_recovers_correction": bool(
                    relation == "semantic_difference"
                    and any(corrected_by_domain.values())
                    and not any(historical_by_domain.values())
                ),
                "question_changed_in_corrected_snapshot": (
                    historical.get("en_question") != corrected.get("en_question")
                ),
            }
        )
    return mapped_results, comparisons


def select_census_controls(
    rows: list[dict[str, Any]],
    *,
    seed: str,
    excluded_row_ids: set[str],
    per_domain_class: int = 5,
) -> dict[str, list[str]]:
    selected: dict[str, list[str]] = {}
    for domain_class in ("stable", "ambiguous"):
        eligible = [
            row
            for row in rows
            if row["target_match"] == "match_both"
            and row["answer_relation"] == "unchanged"
            and row["domain_stability"] == domain_class
            and not row["question_changed_in_corrected_snapshot"]
            and row["row_id"] not in excluded_row_ids
        ]
        ranked = sorted(
            eligible,
            key=lambda row: (
                sha256_text(f"{seed}:{domain_class}:{row['row_id']}"),
                row["row_id"],
            ),
        )
        if len(ranked) < per_domain_class:
            raise NL4OPTError(
                f"requested {per_domain_class} {domain_class} controls, only {len(ranked)} eligible"
            )
        selected[domain_class] = [row["row_id"] for row in ranked[:per_domain_class]]
    return selected


def _revalidation_rows(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    payload = _read_json_object(path)
    results = payload.get("results", [])
    if not isinstance(results, list):
        raise NL4OPTError(f"revalidation summary results must be a list: {path}")
    return _index_rows(results, "row_id", label="July revalidation")


def _modern_july_evidence(
    july_pilot_campaign_dir: Path,
    expected_source_sha256: dict[str, str],
) -> dict[str, dict[str, Any]]:
    pilot = _campaign_outputs_dir(july_pilot_campaign_dir)
    source_rows = read_jsonl(pilot / "source" / "evidence-source-manifest.jsonl")
    source_by_id = _index_rows(source_rows, "row_id", label="July source manifest")
    batch_rows = read_jsonl(pilot / "runs" / "terra-evidence" / "batch-results.jsonl")
    batch_by_id = _index_rows(batch_rows, "row_id", label="July batch result")
    revalidation_by_id = _revalidation_rows(
        pilot / "runs" / "terra-evidence" / "revalidation-summary.json"
    )
    comparison_path = pilot / "comparisons" / "terra-answer-comparison.jsonl"
    comparison_by_id = (
        _index_rows(read_jsonl(comparison_path), "row_id", label="July Terra comparison")
        if comparison_path.is_file()
        else {}
    )
    status: dict[str, dict[str, Any]] = {}
    for row_id, source_row in source_by_id.items():
        reasons: list[str] = []
        expected_hash = expected_source_sha256.get(row_id)
        source_hash = str(source_row.get("source_sha256", ""))
        if expected_hash is None:
            reasons.append("row_not_in_census")
        elif source_hash != expected_hash:
            reasons.append("source_hash_mismatch")
        statement_path = pilot / str(source_row.get("statement_path", ""))
        if not statement_path.is_file():
            reasons.append("source_statement_missing")
        elif sha256_file(statement_path) != source_hash:
            reasons.append("source_statement_hash_mismatch")
        batch = batch_by_id.get(row_id)
        if batch is None:
            reasons.append("batch_result_missing")
            batch = {}
        if batch.get("terminal_status") != "success":
            reasons.append("terminal_status_not_success")
        if batch.get("source_sha256") != source_hash:
            reasons.append("batch_source_hash_mismatch")
        metadata = batch.get("codex_run_metadata")
        metadata = metadata if isinstance(metadata, dict) else {}
        model = batch.get("model") or metadata.get("codex_effective_model")
        effort = batch.get("reasoning_effort") or metadata.get(
            "codex_effective_reasoning_effort"
        )
        if model != "gpt-5.6-terra":
            reasons.append("model_policy_mismatch")
        if effort != "high":
            reasons.append("reasoning_effort_mismatch")
        revalidation = revalidation_by_id.get(row_id)
        validation = revalidation.get("validation", {}) if revalidation else {}
        if (
            not revalidation
            or revalidation.get("effective_terminal_status") != "success"
            or not isinstance(validation, dict)
            or validation.get("status") != "valid"
        ):
            reasons.append("revalidation_not_valid")
        comparison = comparison_by_id.get(row_id)
        if comparison is None:
            reasons.append("comparison_missing")
        elif comparison.get("terminal_status") != "success":
            reasons.append("comparison_not_success")
        workspace = (pilot / "runs" / "terra-evidence" / "rows" / row_id).resolve()
        required_workspace_files = (
            "run-manifest.json",
            "problem.json",
            "audit.json",
            "parent_solver_report.json",
        )
        missing_workspace = [name for name in required_workspace_files if not (workspace / name).is_file()]
        if missing_workspace:
            reasons.append("workspace_artifacts_missing")
        if row_id == "nl4opt-row-0072":
            reasons.append("row0072_modern_evidence_frozen_invalid")
        status[row_id] = {
            "row_id": row_id,
            "source_sha256": source_hash,
            "terminal_status": batch.get("terminal_status", "missing"),
            "revalidation_status": (
                revalidation.get("effective_terminal_status", "missing")
                if revalidation
                else "missing"
            ),
            "model": model,
            "reasoning_effort": effort,
            "terra_workspace": str(workspace),
            "modern_valid": not reasons,
            "invalid_reasons": sorted(set(reasons)),
        }
    return status


def _validate_official_solver_rows(
    *,
    official_targets: list[Any],
    solver_rows: list[dict[str, Any]],
) -> None:
    target_ids = {str(target.source_id) for target in official_targets}
    solver_by_id = _index_rows(solver_rows, "source_id", label="official solver result")
    if set(solver_by_id) != target_ids:
        missing = sorted(target_ids - set(solver_by_id))
        extra = sorted(set(solver_by_id) - target_ids)
        raise NL4OPTError(
            f"official solver source IDs drifted; missing={missing}, extra={extra}"
        )
    targets_by_id = {str(target.source_id): target for target in official_targets}
    failures: list[str] = []
    for source_id, row in solver_by_id.items():
        expected_document_hash = sha256_text(
            str(targets_by_id[source_id].payload["document"])
        )
        if row.get("document_sha256") != expected_document_hash:
            failures.append(f"{source_id}:document_hash")
        for domain in ("continuous", "integer"):
            result = row.get(domain)
            status = result.get("status") if isinstance(result, dict) else None
            if not status or canonical_solver_status(status) == "parse_or_solver_error":
                failures.append(f"{source_id}:{domain}")
    if failures:
        raise NL4OPTError(
            "all-official solver results contain parser/solver/hash failures: "
            + ", ".join(failures[:20])
        )


def _approved_checksum(
    *,
    rows: list[dict[str, Any]],
    valid_reuse_ids: list[str],
    delta_ids: list[str],
    controls: dict[str, list[str]],
    seed: str,
) -> dict[str, Any]:
    target_counts = Counter(row["target_match"] for row in rows)
    relation_counts = Counter(row["answer_relation"] for row in rows)
    domain_counts = Counter(row["domain_stability"] for row in rows)
    candidate_count = sum(bool(row["candidate"]) for row in rows)
    checks: list[tuple[str, Any, Any]] = [
        ("row count", len(rows), APPROVED_ROW_COUNT),
        ("target-match counts", dict(target_counts), APPROVED_TARGET_MATCH_COUNTS),
        ("answer-relation counts", dict(relation_counts), APPROVED_ANSWER_RELATION_COUNTS),
        ("domain-stability counts", dict(domain_counts), APPROVED_DOMAIN_STABILITY_COUNTS),
        ("candidate count", candidate_count, APPROVED_CANDIDATE_COUNT),
        (
            "valid modern July candidate reuse",
            len(valid_reuse_ids),
            APPROVED_JULY_CANDIDATE_REUSE_COUNT,
        ),
        ("Terra candidate delta IDs", tuple(delta_ids), APPROVED_TERRA_DELTA_IDS),
        ("control seed", seed, APPROVED_CONTROL_SEED),
        (
            "stable control IDs",
            tuple(controls["stable"]),
            APPROVED_STABLE_CONTROL_IDS,
        ),
        (
            "ambiguous control IDs",
            tuple(controls["ambiguous"]),
            APPROVED_AMBIGUOUS_CONTROL_IDS,
        ),
    ]
    drift = [f"{name}: observed={observed!r}, expected={expected!r}" for name, observed, expected in checks if observed != expected]
    if drift:
        raise NL4OPTError("approved NL4OPT census checksum drift: " + "; ".join(drift))
    return {
        "rows": len(rows),
        "target_match": {
            key.removeprefix("match_"): target_counts[key]
            for key in APPROVED_TARGET_MATCH_COUNTS
        },
        "answer_relation": dict(relation_counts),
        "domain_stability": dict(domain_counts),
        "candidates": candidate_count,
        "valid_modern_july_candidate_reuse": len(valid_reuse_ids),
        "terra_candidate_delta": len(delta_ids),
        "controls": sum(len(value) for value in controls.values()),
    }


def prepare_nl4opt_census(
    *,
    official_path: Path,
    historical_path: Path,
    corrected_path: Path,
    all_official_solver_results_path: Path,
    july_pilot_campaign_dir: Path,
    output_dir: Path,
    official_commit: str,
    corrected_commit: str,
    seed: str = APPROVED_CONTROL_SEED,
    overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    official_targets = load_official_targets(official_path)
    historical_rows = read_jsonl(historical_path)
    corrected_rows = read_jsonl(corrected_path)
    mappings = map_benchmark_rows(
        historical_rows, corrected_rows, official_targets, overrides=overrides
    )
    unresolved = [row["row_id"] for row in mappings if not row["accepted"]]
    if unresolved:
        raise NL4OPTError("unresolved source mappings: " + ", ".join(unresolved))
    solver_rows = read_jsonl(all_official_solver_results_path)
    _validate_official_solver_rows(
        official_targets=official_targets, solver_rows=solver_rows
    )
    mapped_results, comparisons = classify_census_rows(
        historical_rows=historical_rows,
        corrected_rows=corrected_rows,
        mappings=mappings,
        solver_rows=solver_rows,
    )
    expected_sources = {
        row["row_id"]: sha256_text(_source_text(historical_rows[index].get("en_question")))
        for index, row in enumerate(comparisons)
    }
    july_status = _modern_july_evidence(july_pilot_campaign_dir, expected_sources)
    candidates = [row for row in comparisons if row["candidate"]]
    candidate_ids = {row["row_id"] for row in candidates}
    valid_reuse_ids = sorted(
        row_id
        for row_id, status in july_status.items()
        if row_id in candidate_ids and status["modern_valid"]
    )
    delta_ids = sorted(candidate_ids - set(valid_reuse_ids))
    controls = select_census_controls(
        comparisons,
        seed=seed,
        excluded_row_ids=set(july_status),
    )
    counts = _approved_checksum(
        rows=comparisons,
        valid_reuse_ids=valid_reuse_ids,
        delta_ids=delta_ids,
        controls=controls,
        seed=seed,
    )

    stable_controls = set(controls["stable"])
    ambiguous_controls = set(controls["ambiguous"])
    all_controls = stable_controls | ambiguous_controls
    delta_set = set(delta_ids)
    official_by_id = {str(target.source_id): target.payload for target in official_targets}
    all_source_manifest: list[dict[str, Any]] = []
    hidden_answers: list[dict[str, Any]] = []
    census_rows: list[dict[str, Any]] = []
    comparison_rows: list[dict[str, Any]] = []
    for index, comparison in enumerate(comparisons):
        row_id = comparison["row_id"]
        statement_path = output_dir / "source" / "statements" / f"{row_id}.txt"
        relative_statement_path = str(statement_path.relative_to(output_dir))
        source_hash = expected_sources[row_id]
        control_stratum: str | None = None
        if row_id in candidate_ids:
            census_group = "candidate"
            selection_group = "census_candidate"
        elif row_id in all_controls:
            census_group = "control"
            control_stratum = (
                "stable_control" if row_id in stable_controls else "ambiguous_control"
            )
            selection_group = "unchanged_control"
        else:
            census_group = "background"
            selection_group = "census_background"
        source_row = {
            "row_id": row_id,
            "split": "census",
            "statement_path": relative_statement_path,
            "source_sha256": source_hash,
        }
        all_source_manifest.append(source_row)
        hidden_answers.append(
            {
                "row_id": row_id,
                "selection_group": selection_group,
                "historical_answer": historical_rows[index].get("en_answer"),
                "corrected_answer": corrected_rows[index].get("en_answer"),
                "answer_relation": comparison["answer_relation"],
                "question_changed_in_corrected_snapshot": comparison[
                    "question_changed_in_corrected_snapshot"
                ],
            }
        )
        common = {
            key: value
            for key, value in comparison.items()
            if key not in {"historical_answer", "corrected_answer"}
        }
        common.update(
            {
                "census_group": census_group,
                "selection_group": selection_group,
                "control_stratum": control_stratum,
                "statement_path": relative_statement_path,
                "source_sha256": source_hash,
                "july_modern_valid": july_status.get(row_id, {}).get(
                    "modern_valid", False
                ),
                "terra_delta": row_id in delta_set,
                "fixed_control": row_id in all_controls,
            }
        )
        census_rows.append(common)
        comparison_rows.append({**comparison, "selection_group": selection_group})

    source_by_id = {row["row_id"]: row for row in all_source_manifest}

    def manifest_for(row_ids: Iterable[str], split: str) -> list[dict[str, Any]]:
        return [
            {**source_by_id[row_id], "split": split}
            for row_id in row_ids
        ]

    delta_manifest = manifest_for(delta_ids, "terra_candidate_delta")
    control_ids = [*controls["stable"], *controls["ambiguous"]]
    control_manifest = manifest_for(control_ids, "terra_fixed_control")
    evidence_manifest = [*delta_manifest, *control_manifest]
    if any(set(row) != SOURCE_MANIFEST_FIELDS for row in evidence_manifest):
        raise NL4OPTError("source-only Terra manifest schema drift")

    for index, mapping in enumerate(mappings):
        row_id = mapping["row_id"]
        statement_path = output_dir / source_by_id[row_id]["statement_path"]
        statement_path.parent.mkdir(parents=True, exist_ok=True)
        statement_path.write_text(
            _source_text(historical_rows[index].get("en_question")), encoding="utf-8"
        )
        target_path = output_dir / "source" / "formal-targets" / f"{row_id}.json"
        write_json(
            target_path,
            {
                "row_id": row_id,
                "source_id": mapping["source_id"],
                "official_target": official_by_id[str(mapping["source_id"])],
            },
        )

    write_jsonl(output_dir / "source" / "census-source-manifest.jsonl", all_source_manifest)
    write_jsonl(output_dir / "source" / "evidence-source-manifest.jsonl", evidence_manifest)
    write_jsonl(output_dir / "source" / "terra-delta-source-manifest.jsonl", delta_manifest)
    write_jsonl(output_dir / "source" / "terra-control-source-manifest.jsonl", control_manifest)
    write_jsonl(output_dir / "hidden" / "answer-key.jsonl", hidden_answers)
    write_jsonl(output_dir / "provenance" / "row-mapping.jsonl", mappings)
    write_jsonl(output_dir / "provenance" / "july-modern-evidence.jsonl", july_status.values())
    write_jsonl(output_dir / "deterministic" / "mapped-official-solver-results.jsonl", mapped_results)
    write_jsonl(output_dir / "deterministic" / "formal-target-answer-comparison.jsonl", comparison_rows)
    write_json(
        output_dir / "deterministic" / "census-summary.json",
        {
            "schema_version": "nl4opt_full_census_summary_v1",
            **counts,
        },
    )
    write_jsonl(output_dir / "census" / "census-rows.jsonl", census_rows)
    write_jsonl(output_dir / "census" / "candidate-census.jsonl", candidates)
    selection = {
        "schema_version": "nl4opt_full_census_selection_v1",
        "seed": seed,
        "valid_modern_july_candidate_reuse_ids": valid_reuse_ids,
        "terra_candidate_delta_ids": delta_ids,
        "stable_control_ids": controls["stable"],
        "ambiguous_control_ids": controls["ambiguous"],
        "terra_evidence_row_ids": [row["row_id"] for row in evidence_manifest],
        "answer_blind_manifest": "source/evidence-source-manifest.jsonl",
    }
    write_json(output_dir / "provenance" / "census-selection.json", selection)
    pilot = _campaign_outputs_dir(july_pilot_campaign_dir)
    provenance = {
        "schema_version": "nl4opt_full_benchmark_integrity_census_v1",
        "corpus": "NL4OPT",
        "answer_policy": NL4OPT_ANSWER_POLICY.to_dict(),
        "official": {
            "path": str(official_path.resolve()),
            "sha256": sha256_file(official_path),
            "git_commit": official_commit,
        },
        "historical": {
            "path": str(historical_path.resolve()),
            "sha256": sha256_file(historical_path),
        },
        "corrected": {
            "path": str(corrected_path.resolve()),
            "sha256": sha256_file(corrected_path),
            "git_commit": corrected_commit,
        },
        "all_official_solver_results": {
            "path": str(all_official_solver_results_path.resolve()),
            "sha256": sha256_file(all_official_solver_results_path),
        },
        "july_pilot": {"campaign_dir": str(pilot)},
        "counts": counts,
    }
    write_json(output_dir / "provenance" / "provenance.json", provenance)
    return provenance


def _find_june_manifests(path: Path) -> list[Path]:
    manifests = sorted(path.rglob("stage*_generation_manifest.csv"))
    if not manifests:
        raise NL4OPTError(f"no June stage*_generation_manifest.csv files under {path}")
    return manifests


def _read_june_manifest_rows(paths: list[Path]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for path in paths:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            required = {"case_id", "source_row_index", "question_sha256"}
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise NL4OPTError(f"{path}: missing June manifest columns {sorted(missing)}")
            for line_number, row in enumerate(reader, start=2):
                try:
                    row_number = int(str(row["source_row_index"]))
                except ValueError as exc:
                    raise NL4OPTError(
                        f"{path}:{line_number}: invalid source_row_index"
                    ) from exc
                row_id = f"nl4opt-row-{row_number:04d}"
                case_id = str(row["case_id"])
                if case_id != f"NL4OPT-{row_number:04d}":
                    raise NL4OPTError(
                        f"{path}:{line_number}: case_id/source_row_index mismatch"
                    )
                if row_id in rows:
                    raise NL4OPTError(f"duplicate June evidence row: {row_id}")
                rows[row_id] = {
                    "case_id": case_id,
                    "source_row_index": row_number,
                    "question_sha256": str(row["question_sha256"]),
                    "statement_path": str(row.get("statement_path", "")),
                    "artifact_dir": str(row.get("artifact_dir", "")),
                    "generation_manifest": str(path.resolve()),
                }
    return rows


def reconcile_nl4opt_evidence(
    *,
    campaign_dir: Path,
    june_manifest_dir: Path,
    july_pilot_campaign_dir: Path,
    output_path: Path | None = None,
    summary_path: Path | None = None,
    enforce_approved_counts: bool = True,
) -> dict[str, Any]:
    census_rows = read_jsonl(campaign_dir / "census" / "census-rows.jsonl")
    census_by_id = _index_rows(census_rows, "row_id", label="census")
    source_rows = read_jsonl(campaign_dir / "source" / "census-source-manifest.jsonl")
    source_by_id = _index_rows(source_rows, "row_id", label="census source")
    if set(census_by_id) != set(source_by_id):
        raise NL4OPTError("census rows and census source manifest have different row IDs")
    june_by_id = _read_june_manifest_rows(_find_june_manifests(june_manifest_dir))
    unknown_june = sorted(set(june_by_id) - set(census_by_id))
    if unknown_june:
        raise NL4OPTError("June evidence has unknown rows: " + ", ".join(unknown_june))
    for row_id, june in june_by_id.items():
        census = census_by_id[row_id]
        if june["source_row_index"] != census["dataset_row_number"]:
            raise NL4OPTError(f"{row_id}: June row identity mismatch")
        if june["question_sha256"] != census["dataset_question_sha256"]:
            raise NL4OPTError(f"{row_id}: June dataset question hash mismatch")
    expected_sources = {
        row_id: str(source["source_sha256"]) for row_id, source in source_by_id.items()
    }
    july_by_id = _modern_july_evidence(july_pilot_campaign_dir, expected_sources)
    unknown_july = sorted(set(july_by_id) - set(census_by_id))
    if unknown_july:
        raise NL4OPTError("July evidence has unknown rows: " + ", ".join(unknown_july))
    ledger: list[dict[str, Any]] = []
    for row_id in sorted(census_by_id, key=_row_number):
        june = june_by_id.get(row_id)
        july = july_by_id.get(row_id)
        if june and july:
            evidence_state = "june_plus_july"
        elif june:
            evidence_state = "june_only"
        elif july:
            evidence_state = "july_only"
        else:
            evidence_state = "none"
        ledger.append(
            {
                "row_id": row_id,
                "dataset_row_number": census_by_id[row_id]["dataset_row_number"],
                "dataset_question_sha256": census_by_id[row_id][
                    "dataset_question_sha256"
                ],
                "source_sha256": source_by_id[row_id]["source_sha256"],
                "candidate": bool(census_by_id[row_id]["candidate"]),
                "evidence_state": evidence_state,
                "june_present": june is not None,
                "june_candidate_only": june is not None,
                "june_case_id": june.get("case_id") if june else None,
                "june_artifact_dir": june.get("artifact_dir") if june else None,
                "july_present": july is not None,
                "july_modern_valid": bool(july and july["modern_valid"]),
                "july_terminal_status": july.get("terminal_status") if july else None,
                "july_revalidation_status": (
                    july.get("revalidation_status") if july else None
                ),
                "july_model": july.get("model") if july else None,
                "july_reasoning_effort": july.get("reasoning_effort") if july else None,
                "july_invalid_reasons": july.get("invalid_reasons", []) if july else [],
                "july_terra_workspace": july.get("terra_workspace") if july else None,
            }
        )
    state_counts = Counter(row["evidence_state"] for row in ledger)
    valid_candidate_reuse = sum(
        row["candidate"] and row["july_modern_valid"] for row in ledger
    )
    if enforce_approved_counts:
        if len(ledger) != APPROVED_ROW_COUNT:
            raise NL4OPTError(
                f"evidence reconciliation expected {APPROVED_ROW_COUNT} rows, observed {len(ledger)}"
            )
        if dict(state_counts) != APPROVED_EVIDENCE_STATE_COUNTS:
            raise NL4OPTError(
                "evidence-state checksum drift: "
                f"observed={dict(state_counts)!r}, expected={APPROVED_EVIDENCE_STATE_COUNTS!r}"
            )
        if valid_candidate_reuse != APPROVED_JULY_CANDIDATE_REUSE_COUNT:
            raise NL4OPTError(
                "valid modern July candidate reuse drift: "
                f"observed={valid_candidate_reuse}, expected={APPROVED_JULY_CANDIDATE_REUSE_COUNT}"
            )
        row0072 = next(row for row in ledger if row["row_id"] == "nl4opt-row-0072")
        if row0072["july_modern_valid"]:
            raise NL4OPTError("nl4opt-row-0072 must remain modern invalid")
    output_path = output_path or campaign_dir / "provenance" / "evidence-reconciliation.jsonl"
    summary_path = summary_path or campaign_dir / "provenance" / "evidence-reconciliation-summary.json"
    summary = {
        "schema_version": "nl4opt_evidence_reconciliation_v1",
        "rows": len(ledger),
        "evidence_state_counts": dict(state_counts),
        "june_rows": len(june_by_id),
        "june_candidate_only": True,
        "july_rows": len(july_by_id),
        "july_modern_valid_rows": sum(row["july_modern_valid"] for row in ledger),
        "valid_modern_july_candidate_reuse": valid_candidate_reuse,
        "row0072_modern_valid": bool(
            census_by_id.get("nl4opt-row-0072")
            and july_by_id.get("nl4opt-row-0072", {}).get("modern_valid")
        ),
        "ledger": str(output_path.resolve()),
    }
    write_jsonl(output_path, ledger)
    write_json(summary_path, summary)
    return summary


def _workspace_path(value: Any, *, fallback: Path) -> Path:
    if value:
        path = Path(str(value))
        return path.resolve() if path.is_absolute() else (fallback.parent / path).resolve()
    return fallback.resolve()


def _solver_status_class(result: dict[str, Any]) -> str:
    status = canonical_solver_status(result.get("status", ""))
    if status == "optimal":
        return "optimal"
    if status in {
        "infeasible",
        "unbounded",
        "infeasible_or_unbounded",
        "strict_inequality_infimum_not_attained",
        "unattained_infimum_strict_inequality",
        "infimum_not_attained",
        "unattained_supremum_strict_inequality",
        "supremum_not_attained",
        "strict_inequality_supremum_not_attained",
        "no_attained_minimum_strict_continuous",
        "no_attained_maximum_strict_continuous",
    }:
        return "no_best_solution"
    return status or "missing"


def _objective_equal(left: Any, right: Any) -> bool:
    return isinstance(left, (int, float)) and isinstance(right, (int, float)) and math.isclose(
        float(left), float(right), rel_tol=1e-6, abs_tol=1e-6
    )


def _comparison_report(row: dict[str, Any], workspace: Path) -> dict[str, Any]:
    report_path = workspace / "parent_solver_report.json"
    if report_path.is_file():
        return _read_json_object(report_path)
    return {
        "continuous": {
            "status": row.get("continuous_status"),
            "objective": row.get("continuous_objective"),
        },
        "integer": {
            "status": row.get("integer_status"),
            "objective": row.get("integer_objective"),
        },
    }


def _enrich_terra_comparison(
    *,
    row: dict[str, Any],
    workspace: Path,
    evidence_origin: str,
    census: dict[str, Any],
    official: dict[str, Any],
) -> dict[str, Any]:
    report = _comparison_report(row, workspace)
    solver_status_conflict = False
    numeric_answer_conflict = False
    unresolved = False
    for domain in ("continuous", "integer"):
        generated = report.get(domain, {})
        target = official.get(domain, {})
        if not isinstance(generated, dict) or not isinstance(target, dict):
            unresolved = True
            continue
        generated_class = _solver_status_class(generated)
        target_class = _solver_status_class(target)
        if "missing" in {generated_class, target_class}:
            unresolved = True
        elif generated_class != target_class:
            solver_status_conflict = True
        elif generated_class == "optimal" and not _objective_equal(
            generated.get("objective"), target.get("objective")
        ):
            numeric_answer_conflict = True
    source_target_conflict = solver_status_conflict or numeric_answer_conflict
    domain_ambiguity = bool(
        census.get("domain_ambiguous")
        or row.get("domain_ambiguous")
        or row.get("chosen_domain") == "unresolved"
    )
    terminal_success = row.get("terminal_status") == "success"
    report_complete = all(
        isinstance(report.get(domain), dict) and report[domain].get("status") is not None
        for domain in ("continuous", "integer")
    )
    terra_valid = terminal_success and report_complete and not unresolved
    if not terra_valid:
        interface_class = "unresolved"
    elif source_target_conflict:
        interface_class = "source_target_conflict"
    else:
        interface_class = "source_target_agreement"
    return {
        **row,
        "census_group": census["census_group"],
        "target_match": census["target_match"],
        "evidence_origin": evidence_origin,
        "terra_workspace": str(workspace.resolve()),
        "interface_class": interface_class,
        "source_target_conflict": source_target_conflict,
        "solver_status_conflict": solver_status_conflict,
        "numeric_answer_conflict": numeric_answer_conflict,
        "domain_ambiguity": domain_ambiguity,
        "terra_valid": terra_valid,
    }


def merge_nl4opt_census_terra(
    *,
    campaign_dir: Path,
    july_pilot_campaign_dir: Path,
    delta_comparison_path: Path | None = None,
    delta_run_dir: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    selection = _read_json_object(campaign_dir / "provenance" / "census-selection.json")
    reuse_ids = [str(value) for value in selection["valid_modern_july_candidate_reuse_ids"]]
    delta_ids = [str(value) for value in selection["terra_candidate_delta_ids"]]
    control_ids = [
        *[str(value) for value in selection["stable_control_ids"]],
        *[str(value) for value in selection["ambiguous_control_ids"]],
    ]
    expected_delta_ids = set(delta_ids) | set(control_ids)
    default_delta = campaign_dir / "comparisons" / "terra-answer-comparison.jsonl"
    preserved_delta = campaign_dir / "comparisons" / "terra-delta-answer-comparison.jsonl"
    delta_comparison_path = delta_comparison_path or (
        preserved_delta if preserved_delta.is_file() else default_delta
    )
    delta_rows = read_jsonl(delta_comparison_path)
    delta_by_id = _index_rows(delta_rows, "row_id", label="Terra delta comparison")
    if set(delta_by_id) != expected_delta_ids:
        raise NL4OPTError(
            "Terra delta/control comparison row drift: "
            f"observed={sorted(delta_by_id)}, expected={sorted(expected_delta_ids)}"
        )
    pilot = _campaign_outputs_dir(july_pilot_campaign_dir)
    july_by_id = _index_rows(
        read_jsonl(pilot / "comparisons" / "terra-answer-comparison.jsonl"),
        "row_id",
        label="July Terra comparison",
    )
    missing_reuse = sorted(set(reuse_ids) - set(july_by_id))
    if missing_reuse:
        raise NL4OPTError("July comparison lacks reusable candidates: " + ", ".join(missing_reuse))
    census_by_id = _index_rows(
        read_jsonl(campaign_dir / "census" / "census-rows.jsonl"),
        "row_id",
        label="census",
    )
    official_by_id = _index_rows(
        read_jsonl(campaign_dir / "deterministic" / "mapped-official-solver-results.jsonl"),
        "row_id",
        label="mapped official solver result",
    )
    delta_run_dir = delta_run_dir or campaign_dir / "runs" / "terra-evidence"
    enriched_delta: list[dict[str, Any]] = []
    for row_id in [*delta_ids, *control_ids]:
        row = delta_by_id[row_id]
        workspace = _workspace_path(
            row.get("workspace_path") or row.get("terra_workspace"),
            fallback=delta_run_dir / "rows" / row_id,
        )
        enriched_delta.append(
            _enrich_terra_comparison(
                row=row,
                workspace=workspace,
                evidence_origin="census_delta",
                census=census_by_id[row_id],
                official=official_by_id[row_id],
            )
        )
    reused: list[dict[str, Any]] = []
    for row_id in reuse_ids:
        row = july_by_id[row_id]
        workspace = _workspace_path(
            row.get("workspace_path") or row.get("terra_workspace"),
            fallback=pilot / "runs" / "terra-evidence" / "rows" / row_id,
        )
        enriched = _enrich_terra_comparison(
            row=row,
            workspace=workspace,
            evidence_origin="july_reuse",
            census=census_by_id[row_id],
            official=official_by_id[row_id],
        )
        if not enriched["terra_valid"]:
            raise NL4OPTError(f"reusable July candidate is not valid during merge: {row_id}")
        reused.append(enriched)
    merged = sorted([*reused, *enriched_delta], key=lambda row: _row_number(row["row_id"]))
    merged_ids = [row["row_id"] for row in merged]
    expected_merged = set(reuse_ids) | expected_delta_ids
    if len(merged_ids) != len(set(merged_ids)) or set(merged_ids) != expected_merged:
        raise NL4OPTError("merged Terra comparison has duplicate or missing rows")
    candidate_count = sum(row["census_group"] == "candidate" for row in merged)
    control_count = sum(row["census_group"] == "control" for row in merged)
    if candidate_count != APPROVED_CANDIDATE_COUNT or control_count != 10:
        raise NL4OPTError(
            f"merged Terra checksum drift: candidates={candidate_count}, controls={control_count}"
        )
    output_path = output_path or campaign_dir / "comparisons" / "terra-answer-comparison.jsonl"
    write_jsonl(preserved_delta, enriched_delta)
    write_jsonl(output_path, merged)
    summary = {
        "schema_version": "nl4opt_census_terra_merge_v1",
        "rows": len(merged),
        "candidates": candidate_count,
        "controls": control_count,
        "july_reused_candidates": len(reused),
        "delta_candidates": len(delta_ids),
        "valid_rows": sum(row["terra_valid"] for row in merged),
        "interface_class_counts": dict(Counter(row["interface_class"] for row in merged)),
        "delta_comparison": str(preserved_delta.resolve()),
        "merged_comparison": str(output_path.resolve()),
    }
    write_json(campaign_dir / "comparisons" / "terra-merge-summary.json", summary)
    return summary


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "pass"}


def _priority_categories(row: dict[str, Any]) -> list[str]:
    categories: list[str] = []
    for category in SOL_PRIORITY:
        if category == "source_target_conflict":
            selected = _truthy(row.get(category)) or row.get("interface_class") == category
        else:
            selected = _truthy(row.get(category))
        if selected:
            categories.append(category)
    return categories


def _prior_owner_packet_ids(path: Path | None) -> set[str]:
    if path is None or not path.is_file():
        return set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if "row_id" not in set(reader.fieldnames or []):
            raise NL4OPTError(f"prior owner packet lacks row_id: {path}")
        return {str(row["row_id"]).strip() for row in reader if str(row.get("row_id", "")).strip()}


def select_nl4opt_census_adjudication(
    *,
    campaign_dir: Path,
    terra_comparison_path: Path | None = None,
    prior_owner_packet_path: Path | None = None,
    seed: str = "nl4opt-full-census-sol-v1",
    max_candidates: int = 8,
    max_per_category: int = 2,
    enforce_campaign_gates: bool = True,
) -> dict[str, Any]:
    if not 0 <= max_candidates <= 8:
        raise NL4OPTError("max_candidates must be between 0 and 8")
    if max_per_category != 2:
        raise NL4OPTError("approved census selection requires max_per_category=2")
    terra_comparison_path = terra_comparison_path or campaign_dir / "comparisons" / "terra-answer-comparison.jsonl"
    terra_rows = read_jsonl(terra_comparison_path)
    terra_by_id = _index_rows(terra_rows, "row_id", label="merged Terra comparison")
    if enforce_campaign_gates:
        candidate_rows = [row for row in terra_rows if row.get("census_group") == "candidate"]
        control_rows = [row for row in terra_rows if row.get("census_group") == "control"]
        valid_candidates = sum(
            _truthy(row.get("terra_valid")) and row.get("terminal_status") == "success"
            for row in candidate_rows
        )
        valid_controls = sum(
            _truthy(row.get("terra_valid")) and row.get("terminal_status") == "success"
            for row in control_rows
        )
        validation_path = (
            campaign_dir / "provenance" / "evidence-source-manifest-validation.json"
        )
        validation = _read_json_object(validation_path)
        summary = _read_json_object(
            campaign_dir / "runs" / "terra-evidence" / "batch-summary.json"
        )
        terminal_counts = summary.get("terminal_counts", {})
        if (
            len(candidate_rows) != APPROVED_CANDIDATE_COUNT
            or len(control_rows) != 10
            or valid_candidates < 25
            or valid_controls < 9
            or validation.get("status") != "valid"
            or not _terminal_accounting(summary, 22)
            or not isinstance(terminal_counts, dict)
            or int(terminal_counts.get("leakage_blocked", -1)) != 0
        ):
            raise NL4OPTError(
                "Terra gate failed before Sol selection: "
                f"candidates={valid_candidates}/{len(candidate_rows)}, "
                f"controls={valid_controls}/{len(control_rows)}, "
                f"manifest={validation.get('status')}, "
                f"terminal_accounting={_terminal_accounting(summary, 22)}, "
                f"leakage_blocked={terminal_counts.get('leakage_blocked')}"
            )
    if prior_owner_packet_path is None:
        provenance = _read_json_object(campaign_dir / "provenance" / "provenance.json")
        july_dir = provenance.get("july_pilot", {}).get("campaign_dir")
        if july_dir:
            prior_owner_packet_path = Path(str(july_dir)) / "owner-review" / "owner-review-packet.csv"
    prior_owner_ids = _prior_owner_packet_ids(prior_owner_packet_path)
    eligible = [
        row
        for row in terra_rows
        if row.get("census_group") == "candidate"
        and _truthy(row.get("terra_valid"))
        and row.get("terminal_status") == "success"
        and row.get("answer_relation") != "encoding_equivalent"
        and row["row_id"] not in prior_owner_ids
    ]
    selected: list[tuple[dict[str, Any], str]] = []
    selected_ids: set[str] = set()
    for category in SOL_PRIORITY:
        pool = sorted(
            [
                row
                for row in eligible
                if row["row_id"] not in selected_ids
                and category in _priority_categories(row)
            ],
            key=lambda row: (
                sha256_text(f"{seed}:{category}:{row['row_id']}"),
                row["row_id"],
            ),
        )
        take = min(max_per_category, max_candidates - len(selected))
        for row in pool[:take]:
            selected.append((row, category))
            selected_ids.add(row["row_id"])
        if len(selected) == max_candidates:
            break
    if len(selected) < max_candidates:
        category_rank = {category: index for index, category in enumerate(SOL_PRIORITY)}

        def fill_key(row: dict[str, Any]) -> tuple[int, str, str]:
            categories = _priority_categories(row)
            rank = min((category_rank[item] for item in categories), default=len(SOL_PRIORITY))
            return rank, sha256_text(f"{seed}:fill:{row['row_id']}"), row["row_id"]

        fill = sorted(
            [row for row in eligible if row["row_id"] not in selected_ids],
            key=fill_key,
        )
        for row in fill[: max_candidates - len(selected)]:
            selected.append((row, "deterministic_fill"))
            selected_ids.add(row["row_id"])
    missing_controls = [row_id for row_id in FIXED_SOL_CONTROL_IDS if row_id not in terra_by_id]
    invalid_controls = [
        row_id
        for row_id in FIXED_SOL_CONTROL_IDS
        if row_id in terra_by_id
        and (
            not _truthy(terra_by_id[row_id].get("terra_valid"))
            or terra_by_id[row_id].get("terminal_status") != "success"
        )
    ]
    prior_controls = sorted(set(FIXED_SOL_CONTROL_IDS) & prior_owner_ids)
    if missing_controls or invalid_controls or prior_controls:
        raise NL4OPTError(
            "fixed Sol controls unavailable: "
            f"missing={missing_controls}, invalid={invalid_controls}, prior_owner={prior_controls}"
        )
    source_by_id = _index_rows(
        read_jsonl(campaign_dir / "source" / "census-source-manifest.jsonl"),
        "row_id",
        label="census source",
    )
    selected_candidate_ids = [row["row_id"] for row, _ in selected]
    selected_ids_in_order = [*selected_candidate_ids, *FIXED_SOL_CONTROL_IDS]
    manifest = [
        {
            **source_by_id[row_id],
            "split": "sol_adjudication",
        }
        for row_id in selected_ids_in_order
    ]
    if any(set(row) != SOURCE_MANIFEST_FIELDS for row in manifest):
        raise NL4OPTError("Sol source manifest schema drift or hidden-answer leakage")
    manifest_text = "\n".join(json.dumps(row, sort_keys=True) for row in manifest).lower()
    if any(token in manifest_text for token in ("historical_answer", "corrected_answer", '"answer"')):
        raise NL4OPTError("Sol source manifest contains hidden answer data")
    write_jsonl(campaign_dir / "source" / "sol-source-manifest.jsonl", manifest)
    selection_rows = [
        {
            "row_id": row["row_id"],
            "selection_group": "candidate",
            "priority_category": category,
            "interface_class": row.get("interface_class"),
            "priority_categories": _priority_categories(row),
        }
        for row, category in selected
    ]
    selection_rows.extend(
        {
            "row_id": row_id,
            "selection_group": "fixed_control",
            "priority_category": "fixed_control",
            "interface_class": terra_by_id[row_id].get("interface_class"),
            "priority_categories": _priority_categories(terra_by_id[row_id]),
        }
        for row_id in FIXED_SOL_CONTROL_IDS
    )
    result = {
        "schema_version": "nl4opt_census_sol_selection_v1",
        "status": "frozen",
        "seed": seed,
        "priority": list(SOL_PRIORITY),
        "max_per_category": max_per_category,
        "requested_candidate_cap": max_candidates,
        "eligible_candidates": len(eligible),
        "selected_candidate_row_ids": selected_candidate_ids,
        "fixed_control_row_ids": list(FIXED_SOL_CONTROL_IDS),
        "selected_total": len(manifest),
        "selection": selection_rows,
        "prior_owner_packet": str(prior_owner_packet_path.resolve()) if prior_owner_packet_path else None,
        "prior_owner_packet_row_ids": sorted(prior_owner_ids),
        "answer_blind_manifest": "source/sol-source-manifest.jsonl",
        "hidden_answers_in_manifest": False,
    }
    write_json(campaign_dir / "provenance" / "sol-selection.json", result)
    return result


MAINTENANCE_ACTION_BY_DECISION = {
    "sirl_supported": "replace_dataset_answer_with_sirl_revision",
    "dataset_supported": "retain_dataset_answer_or_repair_official_target",
    "both_valid": "annotate_domain_ambiguity",
    "neither_supported": "recompute_or_exclude_reference_answer",
    "unresolved": "quarantine_for_follow_up",
}


def _read_owner_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"row_id", "owner_decision", "owner_material", "owner_mechanism"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise NL4OPTError(f"owner CSV lacks required columns: {sorted(missing)}")
        rows = [dict(row) for row in reader]
    _index_rows(rows, "row_id", label="owner review")
    return rows


def _terminal_accounting(summary: dict[str, Any] | None, expected: int) -> bool:
    if summary is None:
        return False
    counts = summary.get("terminal_counts")
    if not isinstance(counts, dict):
        return False
    try:
        started = int(summary.get("sessions_started", -1))
        accounted = sum(int(value) for value in counts.values())
    except (TypeError, ValueError):
        return False
    return started == expected and accounted == started


def _comparison_success(row: dict[str, Any] | None) -> bool:
    return bool(row and row.get("terminal_status") == "success")


def _terra_sol_agree(terra: dict[str, Any], sol: dict[str, Any]) -> bool:
    for domain in ("continuous", "integer"):
        terra_status = _solver_status_class(
            {"status": terra.get(f"{domain}_status")}
        )
        sol_status = _solver_status_class({"status": sol.get(f"{domain}_status")})
        if terra_status != sol_status:
            return False
        if terra_status == "optimal" and not _objective_equal(
            terra.get(f"{domain}_objective"), sol.get(f"{domain}_objective")
        ):
            return False
    return True


def finalize_nl4opt_census(
    *,
    campaign_dir: Path,
    terra_comparison_path: Path | None = None,
    sol_comparison_path: Path | None = None,
    owner_csv_path: Path | None = None,
    owner_status_path: Path | None = None,
    census_rows_path: Path | None = None,
    terra_run_summary_path: Path | None = None,
    sol_run_summary_path: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    terra_comparison_path = terra_comparison_path or campaign_dir / "comparisons" / "terra-answer-comparison.jsonl"
    sol_comparison_path = sol_comparison_path or campaign_dir / "comparisons" / "sol-answer-comparison.jsonl"
    owner_csv_path = owner_csv_path or campaign_dir / "owner-review" / "owner-review-packet.csv"
    owner_status_path = owner_status_path or campaign_dir / "owner-review" / "owner-review-status.json"
    census_rows_path = census_rows_path or campaign_dir / "census" / "census-rows.jsonl"
    terra_run_summary_path = terra_run_summary_path or campaign_dir / "runs" / "terra-evidence" / "batch-summary.json"
    sol_run_summary_path = sol_run_summary_path or campaign_dir / "runs" / "sol-adjudication" / "batch-summary.json"
    terra_rows = read_jsonl(terra_comparison_path)
    sol_rows = read_jsonl(sol_comparison_path)
    census_rows = read_jsonl(census_rows_path)
    owner_rows = _read_owner_rows(owner_csv_path)
    owner_status = _read_json_object(owner_status_path)
    terra_by_id = _index_rows(terra_rows, "row_id", label="merged Terra comparison")
    sol_by_id = _index_rows(sol_rows, "row_id", label="Sol comparison")
    census_by_id = _index_rows(census_rows, "row_id", label="census")
    unknown_owner = sorted(
        {row["row_id"] for row in owner_rows} - set(census_by_id)
    )
    if unknown_owner:
        raise NL4OPTError("owner rows are absent from census: " + ", ".join(unknown_owner))
    selection_path = campaign_dir / "provenance" / "census-selection.json"
    census_selection = _read_json_object(selection_path) if selection_path.is_file() else {}
    sol_selection_path = campaign_dir / "provenance" / "sol-selection.json"
    sol_selection = _read_json_object(sol_selection_path) if sol_selection_path.is_file() else {}
    control_ids = {
        *[str(value) for value in census_selection.get("stable_control_ids", [])],
        *[str(value) for value in census_selection.get("ambiguous_control_ids", [])],
    }
    candidate_ids = {
        row_id
        for row_id, row in census_by_id.items()
        if bool(row.get("candidate")) or row.get("census_group") == "candidate"
    }
    expected_terra_ids = candidate_ids | control_ids
    if not expected_terra_ids:
        expected_terra_ids = set(terra_by_id)
    sol_manifest_path = campaign_dir / "source" / "sol-source-manifest.jsonl"
    if sol_manifest_path.is_file():
        expected_sol_ids = {
            row["row_id"] for row in read_jsonl(sol_manifest_path)
        }
    else:
        expected_sol_ids = {row["row_id"] for row in owner_rows}
    delta_expected = len(census_selection.get("terra_candidate_delta_ids", [])) + len(control_ids)
    if delta_expected == 0:
        delta_expected = int(
            _read_json_object(terra_run_summary_path).get("sessions_started", 0)
        ) if terra_run_summary_path.is_file() else 0
    terra_summary = (
        _read_json_object(terra_run_summary_path)
        if terra_run_summary_path.is_file()
        else None
    )
    sol_summary = (
        _read_json_object(sol_run_summary_path)
        if sol_run_summary_path.is_file()
        else None
    )
    owner_vocab_errors: list[str] = []
    actions: list[dict[str, Any]] = []
    prior_owner_ids = set(sol_selection.get("prior_owner_packet_row_ids", []))
    for row in owner_rows:
        row_id = row["row_id"]
        decision = str(row.get("owner_decision", "")).strip()
        material = str(row.get("owner_material", "")).strip()
        mechanism = str(row.get("owner_mechanism", "")).strip()
        if decision not in OWNER_DECISION_VALUES:
            owner_vocab_errors.append(f"{row_id}:owner_decision={decision!r}")
        if material not in OWNER_MATERIAL_VALUES:
            owner_vocab_errors.append(f"{row_id}:owner_material={material!r}")
        if mechanism not in OWNER_MECHANISM_VALUES:
            owner_vocab_errors.append(f"{row_id}:owner_mechanism={mechanism!r}")
        census = census_by_id[row_id]
        is_candidate = row_id in candidate_ids
        material_action = bool(
            decision in OWNER_DECISION_VALUES
            and decision != "unresolved"
            and material == "yes"
            and mechanism in OWNER_MECHANISM_VALUES
            and mechanism != "none"
        )
        terra = terra_by_id.get(row_id, {})
        sol = sol_by_id.get(row_id, {})
        model_agreement = _truthy(row.get("model_agreement")) or (
            bool(terra) and bool(sol) and _terra_sol_agree(terra, sol)
        )
        source_to_target_confirmed = bool(
            material_action
            and _truthy(terra.get("source_target_conflict"))
            and model_agreement
        )
        target_to_answer_confirmed = bool(
            material_action and census.get("target_match") != "match_both"
        )
        actions.append(
            {
                "row_id": row_id,
                "census_group": "candidate" if is_candidate else "control",
                "owner_decision": decision,
                "owner_material": material,
                "owner_mechanism": mechanism,
                "maintenance_action": MAINTENANCE_ACTION_BY_DECISION.get(
                    decision, "invalid_owner_decision"
                ),
                "material_action": material_action,
                "new_candidate_material_action": bool(
                    material_action and is_candidate and row_id not in prior_owner_ids
                ),
                "promoted_control": bool(material_action and not is_candidate),
                "source_to_target_interface_confirmed": source_to_target_confirmed,
                "target_to_answer_interface_confirmed": target_to_answer_confirmed,
            }
        )
    new_candidate_actions = [
        row for row in actions if row["new_candidate_material_action"]
    ]
    mechanisms = {
        row["owner_mechanism"] for row in new_candidate_actions
    }
    promoted_controls = sum(row["promoted_control"] for row in actions)
    source_to_target_confirmed = any(
        row["source_to_target_interface_confirmed"] for row in new_candidate_actions
    )
    target_to_answer_confirmed = any(
        row["target_to_answer_interface_confirmed"] for row in new_candidate_actions
    )
    owner_ids = {row["row_id"] for row in owner_rows}
    valid_terra_candidate_ids = {
        row_id
        for row_id in candidate_ids
        if _truthy(terra_by_id.get(row_id, {}).get("terra_valid"))
        and _comparison_success(terra_by_id.get(row_id))
    }
    valid_terra_control_ids = {
        row_id
        for row_id in control_ids
        if _truthy(terra_by_id.get(row_id, {}).get("terra_valid"))
        and _comparison_success(terra_by_id.get(row_id))
    }
    selected_candidate_ids = expected_sol_ids & candidate_ids
    selected_control_ids = expected_sol_ids & control_ids
    valid_sol_candidate_ids = {
        row_id
        for row_id in selected_candidate_ids
        if _comparison_success(sol_by_id.get(row_id))
    }
    valid_sol_control_ids = {
        row_id
        for row_id in selected_control_ids
        if _comparison_success(sol_by_id.get(row_id))
    }
    valid_sol_ids = valid_sol_candidate_ids | valid_sol_control_ids
    terra_sol_agreement_rows: list[dict[str, Any]] = []
    for row_id in sorted(expected_sol_ids, key=_row_number):
        terra = terra_by_id.get(row_id, {})
        sol = sol_by_id.get(row_id, {})
        terra_sol_agreement_rows.append(
            {
                "row_id": row_id,
                "census_group": (
                    "candidate" if row_id in candidate_ids else "control"
                ),
                "interface_class": terra.get("interface_class"),
                "answer_relation": sol.get("answer_relation"),
                "terra_chosen_domain": terra.get("chosen_domain"),
                "sol_chosen_domain": sol.get("chosen_domain"),
                "domain_assessment_agreement": (
                    terra.get("chosen_domain") == sol.get("chosen_domain")
                ),
                "solver_result_agreement": bool(
                    _comparison_success(terra)
                    and _comparison_success(sol)
                    and _terra_sol_agree(terra, sol)
                ),
                "terra_continuous_status": terra.get("continuous_status"),
                "terra_continuous_objective": terra.get("continuous_objective"),
                "sol_continuous_status": sol.get("continuous_status"),
                "sol_continuous_objective": sol.get("continuous_objective"),
                "terra_integer_status": terra.get("integer_status"),
                "terra_integer_objective": terra.get("integer_objective"),
                "sol_integer_status": sol.get("integer_status"),
                "sol_integer_objective": sol.get("integer_objective"),
            }
        )
    agreeing_sol_ids = {
        row["row_id"]
        for row in terra_sol_agreement_rows
        if row["solver_result_agreement"]
    }
    domain_assessment_agreeing_ids = {
        row["row_id"]
        for row in terra_sol_agreement_rows
        if row["domain_assessment_agreement"]
    }
    solver_agreement_rate = (
        len(agreeing_sol_ids) / len(valid_sol_ids) if valid_sol_ids else 0.0
    )
    unsupported_control_escalations = sum(
        _truthy(sol_by_id.get(row_id, {}).get("unsupported_control_escalation"))
        for row_id in selected_control_ids
    )
    terra_manifest_validation_path = (
        campaign_dir / "provenance" / "evidence-source-manifest-validation.json"
    )
    sol_manifest_validation_path = (
        campaign_dir / "provenance" / "sol-source-manifest-validation.json"
    )
    terra_manifest_validation = (
        _read_json_object(terra_manifest_validation_path)
        if terra_manifest_validation_path.is_file()
        else {}
    )
    sol_manifest_validation = (
        _read_json_object(sol_manifest_validation_path)
        if sol_manifest_validation_path.is_file()
        else {}
    )
    terra_terminal_counts = (
        terra_summary.get("terminal_counts", {}) if terra_summary else {}
    )
    sol_terminal_counts = sol_summary.get("terminal_counts", {}) if sol_summary else {}
    process_gates = {
        "owner_review_complete": owner_status.get("status") == "valid_complete",
        "owner_vocabulary_valid": not owner_vocab_errors,
        "terra_source_manifest_valid": terra_manifest_validation.get("status") == "valid",
        "sol_source_manifest_valid": sol_manifest_validation.get("status") == "valid",
        "terra_zero_leakage": isinstance(terra_terminal_counts, dict)
        and int(terra_terminal_counts.get("leakage_blocked", -1)) == 0,
        "sol_zero_leakage": isinstance(sol_terminal_counts, dict)
        and int(sol_terminal_counts.get("leakage_blocked", -1)) == 0,
        "terra_terminal_accounting": _terminal_accounting(
            terra_summary, delta_expected
        ),
        "sol_terminal_accounting": _terminal_accounting(
            sol_summary, len(expected_sol_ids)
        ),
        "terra_merged_complete": set(terra_by_id) == expected_terra_ids,
        "sol_comparison_complete": set(sol_by_id) == expected_sol_ids,
        "owner_comparisons_successful": all(
            _comparison_success(terra_by_id.get(row_id))
            and _comparison_success(sol_by_id.get(row_id))
            for row_id in owner_ids
        ),
    }
    process_pass = all(process_gates.values())
    evidence_gates = {
        "terra_candidate_coverage": len(valid_terra_candidate_ids) >= 25,
        "terra_control_coverage": len(valid_terra_control_ids) >= 9,
        "sol_candidate_coverage": len(valid_sol_candidate_ids) >= 7,
        "sol_control_coverage": len(valid_sol_control_ids) >= 3,
        "sol_solver_agreement": solver_agreement_rate >= 0.8,
        "max_unsupported_control_escalations": unsupported_control_escalations <= 1,
        "min_new_candidate_material_actions": len(new_candidate_actions) >= 3,
        "min_distinct_mechanisms": len(mechanisms) >= 2,
        "max_promoted_controls": promoted_controls <= 1,
        "source_to_target_interface_confirmed": source_to_target_confirmed,
        "target_to_answer_interface_confirmed": target_to_answer_confirmed,
    }
    machine_process_gate_names = {
        "terra_source_manifest_valid",
        "sol_source_manifest_valid",
        "terra_zero_leakage",
        "sol_zero_leakage",
        "terra_terminal_accounting",
        "sol_terminal_accounting",
        "terra_merged_complete",
        "sol_comparison_complete",
        "owner_comparisons_successful",
    }
    machine_evidence_gate_names = {
        "terra_candidate_coverage",
        "terra_control_coverage",
        "sol_candidate_coverage",
        "sol_control_coverage",
        "sol_solver_agreement",
        "max_unsupported_control_escalations",
    }
    machine_gate_pass = all(
        process_gates[name] for name in machine_process_gate_names
    ) and all(evidence_gates[name] for name in machine_evidence_gate_names)
    positive_gate_pass = process_pass and all(evidence_gates.values())
    if not machine_gate_pass:
        verdict = "park_pre_owner_machine_gate_failure"
        next_route = "park_stop_scaling"
        next_route_label = "park/stop scaling"
    elif owner_status.get("status") == "pending":
        verdict = "blocked_owner_review"
        next_route = "blocked_owner_review"
        next_route_label = "blocked owner review"
    elif positive_gate_pass:
        verdict = "continue_to_evaluation_impact_campaign"
        next_route = "evaluation_impact_campaign"
        next_route_label = "evaluation-impact campaign"
    else:
        verdict = "park_and_stop_model_scaling"
        next_route = "park_stop_scaling"
        next_route_label = "park/stop scaling"
    owner_review_required = machine_gate_pass
    reported_owner_status = (
        owner_status.get("status")
        if owner_review_required
        else "skipped_pre_owner_machine_gate_failure"
    )
    output_path = output_path or campaign_dir / "comparisons" / "final-gate-summary.json"
    summary = {
        "schema_version": "nl4opt_full_census_final_gate_v1",
        "verdict": verdict,
        "next_route": next_route,
        "next_route_label": next_route_label,
        "paper_writing_allowed": False,
        "owner_review_required": owner_review_required,
        "owner_status": reported_owner_status,
        "owner_source_status": owner_status.get("status"),
        "owner_vocabulary_errors": owner_vocab_errors,
        "maintenance_action_rows": len(actions),
        "new_candidate_material_action_count": len(new_candidate_actions),
        "new_candidate_material_action_row_ids": [
            row["row_id"] for row in new_candidate_actions
        ],
        "confirmed_mechanisms": sorted(mechanisms),
        "confirmed_mechanism_count": len(mechanisms),
        "promoted_control_count": promoted_controls,
        "terra_valid_candidate_count": len(valid_terra_candidate_ids),
        "terra_valid_control_count": len(valid_terra_control_ids),
        "sol_valid_candidate_count": len(valid_sol_candidate_ids),
        "sol_valid_control_count": len(valid_sol_control_ids),
        "sol_solver_agreement_count": len(agreeing_sol_ids),
        "sol_solver_agreement_denominator": len(valid_sol_ids),
        "sol_solver_agreement_rate": solver_agreement_rate,
        "sol_solver_agreement_row_ids": sorted(agreeing_sol_ids, key=_row_number),
        "sol_solver_disagreement_row_ids": sorted(
            valid_sol_ids - agreeing_sol_ids, key=_row_number
        ),
        "sol_domain_assessment_agreement_count": len(domain_assessment_agreeing_ids),
        "sol_domain_assessment_agreement_row_ids": sorted(
            domain_assessment_agreeing_ids, key=_row_number
        ),
        "unsupported_control_escalation_count": unsupported_control_escalations,
        "process_gates": process_gates,
        "process_gates_pass": process_pass,
        "evidence_gates": evidence_gates,
        "machine_process_gate_names": sorted(machine_process_gate_names),
        "machine_evidence_gate_names": sorted(machine_evidence_gate_names),
        "machine_gate_pass": machine_gate_pass,
        "positive_gate_pass": positive_gate_pass,
        "requirements": {
            "min_new_candidate_material_actions": 3,
            "min_distinct_mechanisms": 2,
            "max_promoted_controls": 1,
            "min_terra_valid_candidates": 25,
            "min_terra_valid_controls": 9,
            "min_sol_valid_candidates": 7,
            "min_sol_valid_controls": 3,
            "min_sol_solver_agreement_rate": 0.8,
            "max_unsupported_control_escalations": 1,
            "requires_source_to_target_interface_evidence": True,
            "requires_target_to_answer_interface_evidence": True,
        },
    }
    write_jsonl(campaign_dir / "comparisons" / "maintenance-actions.jsonl", actions)
    write_jsonl(
        campaign_dir / "comparisons" / "terra-sol-agreement.jsonl",
        terra_sol_agreement_rows,
    )
    maintenance_csv = campaign_dir / "comparisons" / "maintenance-actions.csv"
    maintenance_csv.parent.mkdir(parents=True, exist_ok=True)
    with maintenance_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(actions[0]) if actions else ["row_id"])
        writer.writeheader()
        writer.writerows(actions)
    write_json(output_path, summary)
    write_json(
        campaign_dir / "route_decision.json",
        {
            "decision_id": "D-nl4opt-full-benchmark-integrity-census-v1",
            **summary,
            "claims_not_made": [
                "fresh-sample benchmark fault prevalence",
                "universal detector performance",
                "cross-dataset generality",
                "paper readiness",
            ],
        },
    )
    return summary
