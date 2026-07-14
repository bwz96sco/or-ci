from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from or_ci.benchmark_answers import (
    MAMO_EASYLP_ANSWER_POLICY,
    answer_relation,
)
from or_ci.nl4opt_audit import (
    NL4OPTError,
    read_jsonl,
    sha256_file,
    sha256_text,
    write_json,
    write_jsonl,
)


class MAMOAuditError(NL4OPTError):
    pass


MAMO_DATASET_ID_RE = re.compile(r"MAMO_EASYLP-(\d{4})", re.IGNORECASE)


def _row_id(index: int) -> str:
    return f"mamo-easylp-row-{index:04d}"


def _dataset_id(index: int) -> str:
    return f"MAMO_EASYLP-{index:04d}"


def _statement_text(row: dict[str, Any], *, index: int) -> str:
    question = row.get("en_question")
    if not isinstance(question, str) or not question.strip():
        raise MAMOAuditError(f"MAMO row {index} has no en_question")
    return question.rstrip() + "\n"


def _load_index_set(payload: dict[str, Any], field: str) -> set[int]:
    values = payload.get(field)
    if not isinstance(values, list) or any(not isinstance(value, int) for value in values):
        raise MAMOAuditError(f"correction manifest {field} must be a list of integers")
    result = set(values)
    if len(result) != len(values):
        raise MAMOAuditError(f"correction manifest {field} contains duplicates")
    return result


def scan_opened_mamo_rows(
    *,
    experiments_root: Path,
    original_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    original_rows = read_jsonl(original_path)
    evidence: dict[int, list[Path]] = {}
    for events_path in experiments_root.rglob("codex-events.jsonl"):
        matches = {int(value) for value in MAMO_DATASET_ID_RE.findall(str(events_path))}
        for index in matches:
            if 0 <= index < len(original_rows):
                evidence.setdefault(index, []).append(events_path)

    rows: list[dict[str, Any]] = []
    for index, paths in sorted(evidence.items()):
        statement = _statement_text(original_rows[index], index=index)
        rows.append(
            {
                "row_id": _row_id(index),
                "dataset_id": _dataset_id(index),
                "dataset_index_zero": index,
                "source_sha256": sha256_text(statement),
                "event_file_count": len(paths),
                "session_stages": sorted({path.parent.name for path in paths}),
                "evidence_paths": [str(path.resolve()) for path in sorted(paths)],
            }
        )
    write_jsonl(output_path, rows)
    summary = {
        "schema_version": "mamo_opened_row_ledger_v1",
        "status": "complete",
        "dataset": "MAMO_EasyLP",
        "source_path": str(original_path.resolve()),
        "source_sha256": sha256_file(original_path),
        "experiments_root": str(experiments_root.resolve()),
        "opened_rows": len(rows),
        "codex_event_files": sum(row["event_file_count"] for row in rows),
        "ledger": str(output_path.resolve()),
    }
    write_json(output_path.with_suffix(".summary.json"), summary)
    return summary


def _opened_indices(opened_manifest_path: Path) -> set[int]:
    opened: set[int] = set()
    for line_number, row in enumerate(read_jsonl(opened_manifest_path), start=1):
        value = row.get("dataset_index_zero")
        if not isinstance(value, int) or value < 0:
            raise MAMOAuditError(
                f"{opened_manifest_path}:{line_number}: invalid dataset_index_zero"
            )
        if value in opened:
            raise MAMOAuditError(f"opened-row manifest contains duplicate index {value}")
        opened.add(value)
    return opened


def _ranked(indices: Iterable[int], *, seed: str) -> list[int]:
    return sorted(indices, key=lambda index: sha256_text(f"{seed}:{_row_id(index)}"))


def _mamo_evaluation_contract(
    *,
    corrected_rows: int,
    control_rows: int,
    min_revised_recovery: int,
    min_revision_discrimination: int,
    max_control_disagreement: int,
) -> dict[str, int]:
    counts = {
        "corrected_rows": corrected_rows,
        "control_rows": control_rows,
        "min_revised_recovery": min_revised_recovery,
        "min_revision_discrimination": min_revision_discrimination,
        "max_control_disagreement": max_control_disagreement,
    }
    for name, value in counts.items():
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise MAMOAuditError(f"MAMO evaluation contract {name} must be a nonnegative integer")
    if corrected_rows <= 0 or control_rows <= 0:
        raise MAMOAuditError("corrected and control counts must be positive")
    if min_revised_recovery > corrected_rows:
        raise MAMOAuditError("minimum revised recovery exceeds corrected-row count")
    if min_revision_discrimination > corrected_rows:
        raise MAMOAuditError("minimum revision discrimination exceeds corrected-row count")
    if max_control_disagreement > control_rows:
        raise MAMOAuditError("maximum control disagreement exceeds control-row count")
    return {
        **counts,
        "required_terra_rows": corrected_rows + control_rows,
    }


def _campaign_evaluation_contract(campaign_dir: Path) -> dict[str, int]:
    provenance_path = campaign_dir / "provenance" / "provenance.json"
    if not provenance_path.is_file():
        return _mamo_evaluation_contract(
            corrected_rows=20,
            control_rows=20,
            min_revised_recovery=15,
            min_revision_discrimination=12,
            max_control_disagreement=3,
        )
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    contract = provenance.get("evaluation_contract") if isinstance(provenance, dict) else None
    if contract is None:
        return _mamo_evaluation_contract(
            corrected_rows=20,
            control_rows=20,
            min_revised_recovery=15,
            min_revision_discrimination=12,
            max_control_disagreement=3,
        )
    if not isinstance(contract, dict):
        raise MAMOAuditError("MAMO provenance evaluation_contract must be an object")
    required_fields = {
        "corrected_rows",
        "control_rows",
        "min_revised_recovery",
        "min_revision_discrimination",
        "max_control_disagreement",
    }
    if not required_fields.issubset(contract):
        missing = sorted(required_fields - set(contract))
        raise MAMOAuditError(f"MAMO evaluation contract missing fields: {missing}")
    return _mamo_evaluation_contract(
        corrected_rows=contract["corrected_rows"],
        control_rows=contract["control_rows"],
        min_revised_recovery=contract["min_revised_recovery"],
        min_revision_discrimination=contract["min_revision_discrimination"],
        max_control_disagreement=contract["max_control_disagreement"],
    )


def prepare_mamo_replication(
    *,
    original_path: Path,
    revised_path: Path,
    correction_manifest_path: Path,
    opened_manifest_path: Path,
    output_dir: Path,
    original_commit: str,
    revised_commit: str,
    seed: str,
    corrected_count: int,
    control_count: int,
    min_revised_recovery: int = 15,
    min_revision_discrimination: int = 12,
    max_control_disagreement: int = 3,
) -> dict[str, Any]:
    evaluation_contract = _mamo_evaluation_contract(
        corrected_rows=corrected_count,
        control_rows=control_count,
        min_revised_recovery=min_revised_recovery,
        min_revision_discrimination=min_revision_discrimination,
        max_control_disagreement=max_control_disagreement,
    )
    original_rows = read_jsonl(original_path)
    revised_rows = read_jsonl(revised_path)
    correction_manifest = json.loads(correction_manifest_path.read_text(encoding="utf-8"))
    if not isinstance(correction_manifest, dict):
        raise MAMOAuditError("correction manifest must be a JSON object")
    if correction_manifest.get("index_base") != 0:
        raise MAMOAuditError("correction manifest index_base must be 0")
    removed = _load_index_set(correction_manifest, "removed_indices")
    question_revisions = _load_index_set(correction_manifest, "question_revision_indices")
    answer_corrections = _load_index_set(correction_manifest, "answer_correction_indices")
    if removed & question_revisions:
        raise MAMOAuditError("removed and question-revision indices overlap")
    if removed & answer_corrections:
        raise MAMOAuditError("removed and answer-correction indices overlap")
    if len(revised_rows) != len(original_rows) - len(removed):
        raise MAMOAuditError(
            "revised row count does not equal original count minus declared removals"
        )
    all_declared = removed | question_revisions | answer_corrections
    invalid_declared = sorted(index for index in all_declared if not 0 <= index < len(original_rows))
    if invalid_declared:
        raise MAMOAuditError(f"correction manifest indices are out of range: {invalid_declared}")

    opened = _opened_indices(opened_manifest_path)
    invalid_opened = sorted(index for index in opened if index >= len(original_rows))
    if invalid_opened:
        raise MAMOAuditError(f"opened-row indices are out of range: {invalid_opened}")
    revised_by_question: dict[str, list[int]] = {}
    for index, row in enumerate(revised_rows):
        question = row.get("en_question")
        if isinstance(question, str):
            revised_by_question.setdefault(question, []).append(index)
    mappings: list[dict[str, Any]] = []
    corrected_candidates: list[int] = []
    control_candidates: list[int] = []
    for index, original in enumerate(original_rows):
        row_id = _row_id(index)
        if index in removed:
            mappings.append(
                {
                    "row_id": row_id,
                    "dataset_index_zero": index,
                    "revised_index_zero": None,
                    "eligibility": "excluded",
                    "exclusion_reason": "removed_by_revision_source",
                }
            )
            continue
        original_question = original.get("en_question")
        matches = (
            revised_by_question.get(original_question, [])
            if isinstance(original_question, str)
            else []
        )
        current_revised_index = matches[0] if len(matches) == 1 else None
        revised = revised_rows[current_revised_index] if current_revised_index is not None else None
        question_equal = revised is not None
        relation = (
            answer_relation(
                original.get("en_answer"),
                revised.get("en_answer"),
                policy=MAMO_EASYLP_ANSWER_POLICY,
            )
            if revised is not None
            else "unmapped"
        )
        reason = "eligible"
        eligibility = "excluded"
        if index in question_revisions:
            reason = "declared_question_revision"
        elif len(matches) > 1:
            reason = "duplicate_revised_question"
        elif not question_equal:
            reason = "undeclared_question_drift"
        elif index in opened:
            reason = "prior_nested_codex_session"
        elif index in answer_corrections and relation == "semantic_difference":
            eligibility = "corrected_candidate"
            corrected_candidates.append(index)
        elif index in answer_corrections:
            reason = f"declared_correction_{relation}"
        elif relation == "unchanged":
            eligibility = "control_candidate"
            control_candidates.append(index)
        else:
            reason = f"unlisted_answer_{relation}"
        mappings.append(
            {
                "row_id": row_id,
                "dataset_index_zero": index,
                "revised_index_zero": current_revised_index,
                "question_equal": question_equal,
                "answer_relation": relation,
                "prior_nested_codex_session": index in opened,
                "eligibility": eligibility,
                "exclusion_reason": None if eligibility != "excluded" else reason,
            }
        )

    ranked_corrected = _ranked(
        corrected_candidates,
        seed=f"{seed}:corrected",
    )
    ranked_controls = _ranked(
        control_candidates,
        seed=f"{seed}:control",
    )
    enough_candidates = (
        len(ranked_corrected) >= corrected_count and len(ranked_controls) >= control_count
    )
    selected_corrected = ranked_corrected[:corrected_count] if enough_candidates else []
    selected_controls = ranked_controls[:control_count] if enough_candidates else []

    provenance = {
        "schema_version": "mamo_benchmark_integrity_provenance_v2",
        "status": "frozen" if enough_candidates else "blocked_candidate_shortfall",
        "corpus": "MAMO_EasyLP",
        "original": {
            "path": str(original_path.resolve()),
            "sha256": sha256_file(original_path),
            "git_commit": original_commit,
        },
        "revised": {
            "path": str(revised_path.resolve()),
            "sha256": sha256_file(revised_path),
            "git_commit": revised_commit,
            "repository": "https://github.com/Cardinal-Operations/SIRL",
        },
        "correction_manifest": {
            "path": str(correction_manifest_path.resolve()),
            "sha256": sha256_file(correction_manifest_path),
        },
        "opened_manifest": {
            "path": str(opened_manifest_path.resolve()),
            "sha256": sha256_file(opened_manifest_path),
            "opened_rows": len(opened),
        },
        "answer_policy": MAMO_EASYLP_ANSWER_POLICY.to_dict(),
        "evaluation_contract": evaluation_contract,
        "selection": {
            "seed": seed,
            "algorithm": "lowest SHA256(seed:stratum:row_id)",
            "required_corrected": corrected_count,
            "required_controls": control_count,
            "selected_corrected_row_ids": [_row_id(index) for index in selected_corrected],
            "selected_control_row_ids": [_row_id(index) for index in selected_controls],
        },
        "counts": {
            "original_rows": len(original_rows),
            "revised_rows": len(revised_rows),
            "opened_rows": len(opened),
            "eligible_corrected_candidates": len(ranked_corrected),
            "eligible_control_candidates": len(ranked_controls),
            "selected_corrected": len(selected_corrected),
            "selected_controls": len(selected_controls),
        },
    }
    write_jsonl(output_dir / "provenance" / "row-mapping-and-exclusions.jsonl", mappings)
    write_json(
        output_dir / "provenance" / "candidate-inventory.json",
        {
            "status": provenance["status"],
            "corrected_candidate_row_ids": [_row_id(index) for index in ranked_corrected],
            "control_candidate_row_ids": [_row_id(index) for index in ranked_controls],
            "counts": provenance["counts"],
        },
    )
    write_json(output_dir / "provenance" / "provenance.json", provenance)

    if not enough_candidates:
        raise MAMOAuditError(
            "MAMO candidate shortfall: "
            f"required {corrected_count} corrected/{control_count} controls, observed "
            f"{len(ranked_corrected)} corrected/{len(ranked_controls)} controls"
        )

    source_manifest: list[dict[str, Any]] = []
    hidden_answers: list[dict[str, Any]] = []
    selected = [(index, "answer_changed") for index in selected_corrected]
    selected.extend((index, "unchanged_control") for index in selected_controls)
    mapping_by_index = {row["dataset_index_zero"]: row for row in mappings}
    for index, selection_group in selected:
        row_id = _row_id(index)
        statement_path = output_dir / "source" / "statements" / f"{row_id}.txt"
        statement_path.parent.mkdir(parents=True, exist_ok=True)
        statement_path.write_text(_statement_text(original_rows[index], index=index), encoding="utf-8")
        revised_row = revised_rows[mapping_by_index[index]["revised_index_zero"]]
        source_manifest.append(
            {
                "row_id": row_id,
                "split": "mamo_replication_evidence",
                "statement_path": str(statement_path.relative_to(output_dir)),
                "source_sha256": sha256_file(statement_path),
            }
        )
        hidden_answers.append(
            {
                "row_id": row_id,
                "dataset_index_zero": index,
                "selection_group": selection_group,
                "historical_answer": original_rows[index].get("en_answer"),
                "corrected_answer": revised_row.get("en_answer"),
                "answer_relation": answer_relation(
                    original_rows[index].get("en_answer"),
                    revised_row.get("en_answer"),
                    policy=MAMO_EASYLP_ANSWER_POLICY,
                ),
            }
        )
    write_jsonl(output_dir / "source" / "evidence-source-manifest.jsonl", source_manifest)
    canary_ids = {_row_id(selected_corrected[0]), _row_id(selected_controls[0])}
    write_jsonl(
        output_dir / "source" / "canary-source-manifest.jsonl",
        [{**row, "split": "mamo_replication_canary"} for row in source_manifest if row["row_id"] in canary_ids],
    )
    write_jsonl(output_dir / "hidden" / "answer-key.jsonl", hidden_answers)
    return provenance


def _take_ranked(
    target: list[dict[str, Any]],
    candidates: Iterable[dict[str, Any]],
    *,
    count: int,
    seed: str,
) -> None:
    selected_ids = {row["row_id"] for row in target}
    ranked = sorted(
        (row for row in candidates if row["row_id"] not in selected_ids),
        key=lambda row: sha256_text(f"{seed}:{row['row_id']}"),
    )
    target.extend(ranked[:count])


def select_mamo_adjudication(
    *,
    campaign_dir: Path,
    terra_comparison_path: Path,
    seed: str,
) -> dict[str, Any]:
    contract = _campaign_evaluation_contract(campaign_dir)
    rows = read_jsonl(terra_comparison_path)
    corrected = [row for row in rows if row.get("selection_group") == "answer_changed"]
    controls = [row for row in rows if row.get("selection_group") == "unchanged_control"]
    valid = sum(row.get("terminal_status") == "success" for row in rows)
    recovery = sum(bool(row.get("revised_reproduced_selected_domain")) for row in corrected)
    discrimination = sum(bool(row.get("revised_discriminated_selected_domain")) for row in corrected)
    control_disagreement = sum(
        bool(row.get("unchanged_control_disagreement_selected_domain")) for row in controls
    )
    gates = {
        "valid_terra_rows": {
            "observed": valid,
            "required": contract["required_terra_rows"],
            "pass": valid == contract["required_terra_rows"],
        },
        "revised_recovery": {
            "observed": recovery,
            "required_minimum": contract["min_revised_recovery"],
            "pass": recovery >= contract["min_revised_recovery"],
        },
        "revision_discrimination": {
            "observed": discrimination,
            "required_minimum": contract["min_revision_discrimination"],
            "pass": discrimination >= contract["min_revision_discrimination"],
        },
        "control_disagreement": {
            "observed": control_disagreement,
            "required_maximum": contract["max_control_disagreement"],
            "pass": control_disagreement <= contract["max_control_disagreement"],
        },
    }
    gate_pass = (
        len(corrected) == contract["corrected_rows"]
        and len(controls) == contract["control_rows"]
        and all(gate["pass"] for gate in gates.values())
    )
    result: dict[str, Any] = {
        "schema_version": "mamo_sol_selection_v2",
        "status": "blocked_terra_gate" if not gate_pass else "frozen",
        "seed": seed,
        "evaluation_contract": contract,
        "gates": gates,
        "corrected_rows": len(corrected),
        "control_rows": len(controls),
        "selected_row_ids": [],
        "selection_strata": {},
    }
    selection_path = campaign_dir / "provenance" / "sol-selection.json"
    if not gate_pass:
        write_json(selection_path, result)
        return result

    corrected_success = [row for row in corrected if row.get("revised_discriminated_selected_domain")]
    corrected_ambiguous = [
        row
        for row in corrected
        if row.get("domain_ambiguous") or row.get("chosen_domain") == "unresolved"
    ]
    corrected_failure = [
        row
        for row in corrected
        if row not in corrected_success and row not in corrected_ambiguous
    ]
    selected_corrected: list[dict[str, Any]] = []
    _take_ranked(selected_corrected, corrected_success, count=4, seed=f"{seed}:corrected-success")
    _take_ranked(selected_corrected, corrected_failure, count=2, seed=f"{seed}:corrected-failure")
    _take_ranked(selected_corrected, corrected_ambiguous, count=2, seed=f"{seed}:corrected-ambiguous")
    _take_ranked(
        selected_corrected,
        corrected,
        count=8 - len(selected_corrected),
        seed=f"{seed}:corrected-fill",
    )

    escalated_controls = [
        row for row in controls if row.get("unchanged_control_disagreement_selected_domain")
    ]
    clean_controls = [row for row in controls if row not in escalated_controls]
    selected_controls: list[dict[str, Any]] = []
    _take_ranked(
        selected_controls,
        escalated_controls,
        count=min(3, len(escalated_controls)),
        seed=f"{seed}:control-escalated",
    )
    _take_ranked(
        selected_controls,
        clean_controls,
        count=4 - len(selected_controls),
        seed=f"{seed}:control-clean",
    )
    if len(selected_corrected) != 8 or len(selected_controls) != 4:
        raise MAMOAuditError("could not construct the frozen 8+4 Sol adjudication set")

    selected_rows = [*selected_corrected, *selected_controls]
    source_by_id = {
        row["row_id"]: row
        for row in read_jsonl(campaign_dir / "source" / "evidence-source-manifest.jsonl")
    }
    sol_manifest = [
        {**source_by_id[row["row_id"]], "split": "sol_adjudication"}
        for row in selected_rows
    ]
    write_jsonl(campaign_dir / "source" / "sol-source-manifest.jsonl", sol_manifest)
    result.update(
        {
            "selected_row_ids": [row["row_id"] for row in selected_rows],
            "selection_strata": {
                "corrected_success_available": len(corrected_success),
                "corrected_failure_available": len(corrected_failure),
                "corrected_ambiguous_available": len(corrected_ambiguous),
                "escalated_controls_available": len(escalated_controls),
                "clean_controls_available": len(clean_controls),
            },
        }
    )
    write_json(selection_path, result)
    return result
