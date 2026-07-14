from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

from or_ci.benchmark_answers import AnswerPolicy, canonical_solver_status, result_matches_answer
from or_ci.nl4opt_audit import read_jsonl, sha256_file, sha256_text, write_json, write_jsonl


class InterpretationAuditError(ValueError):
    pass


INDUSTRYOR_ID_RE = re.compile(r"INDUSTRYOR[-_](\d{1,4})", re.IGNORECASE)
DIFFICULTIES = ("Easy", "Medium", "Hard")
TERMINAL_STATES = {
    "success",
    "model_failed",
    "artifact_invalid",
    "solver_failed",
    "leakage_blocked",
    "timed_out",
}
SUPPORT_CATEGORIES = {
    "robustly_supported",
    "partially_supported",
    "unsupported_within_enumerated_set",
    "unresolved",
}
INDUSTRYOR_ANSWER_POLICY = AnswerPolicy(
    name="industryor_v1",
    status_sentinels=(-99999.0,),
    absolute_tolerance=0.005,
    relative_tolerance=1e-6,
    solver_absolute_tolerance=0.005,
    solver_relative_tolerance=1e-6,
)


def _dataset_id(value: int) -> str:
    return f"INDUSTRYOR-{value}"


def _row_id(value: int) -> str:
    return f"industryor-row-{value:04d}"


def _statement_text(row: dict[str, Any], *, dataset_id: int) -> str:
    value = row.get("en_question")
    if not isinstance(value, str) or not value.strip():
        raise InterpretationAuditError(f"IndustryOR row {dataset_id} has no en_question")
    return value.rstrip() + "\n"


def _load_industryor(path: Path) -> list[dict[str, Any]]:
    rows = read_jsonl(path)
    seen: set[int] = set()
    for line_number, row in enumerate(rows, start=1):
        value = row.get("id")
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise InterpretationAuditError(f"{path}:{line_number}: invalid IndustryOR id")
        if value in seen:
            raise InterpretationAuditError(f"{path}:{line_number}: duplicate IndustryOR id {value}")
        seen.add(value)
        if row.get("difficulty") not in DIFFICULTIES:
            raise InterpretationAuditError(f"{path}:{line_number}: invalid difficulty")
        if "en_answer" not in row:
            raise InterpretationAuditError(f"{path}:{line_number}: missing en_answer")
        _statement_text(row, dataset_id=value)
    return rows


def scan_opened_industryor_rows(
    *,
    experiments_root: Path,
    dataset_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    rows = _load_industryor(dataset_path)
    known_ids = {row["id"] for row in rows}
    evidence: dict[int, list[Path]] = {}
    for events_path in experiments_root.rglob("codex-events.jsonl"):
        for raw in INDUSTRYOR_ID_RE.findall(str(events_path)):
            value = int(raw)
            if value in known_ids:
                evidence.setdefault(value, []).append(events_path)
    ledger: list[dict[str, Any]] = []
    by_id = {row["id"]: row for row in rows}
    for value, paths in sorted(evidence.items()):
        statement = _statement_text(by_id[value], dataset_id=value)
        ledger.append(
            {
                "row_id": _row_id(value),
                "dataset_id": _dataset_id(value),
                "dataset_numeric_id": value,
                "source_sha256": sha256_text(statement),
                "event_file_count": len(paths),
                "session_stages": sorted({path.parent.name for path in paths}),
                "evidence_paths": [str(path.resolve()) for path in sorted(paths)],
            }
        )
    write_jsonl(output_path, ledger)
    summary = {
        "schema_version": "industryor_opened_row_ledger_v1",
        "status": "complete",
        "dataset": "IndustryOR",
        "dataset_path": str(dataset_path.resolve()),
        "dataset_sha256": sha256_file(dataset_path),
        "experiments_root": str(experiments_root.resolve()),
        "opened_rows": len(ledger),
        "codex_event_files": sum(row["event_file_count"] for row in ledger),
        "ledger": str(output_path.resolve()),
    }
    write_json(output_path.with_suffix(".summary.json"), summary)
    return summary


def _opened_numeric_ids(path: Path) -> set[int]:
    opened: set[int] = set()
    for line_number, row in enumerate(read_jsonl(path), start=1):
        value = row.get("dataset_numeric_id")
        if not isinstance(value, int) or value <= 0:
            raise InterpretationAuditError(f"{path}:{line_number}: invalid dataset_numeric_id")
        if value in opened:
            raise InterpretationAuditError(f"{path}:{line_number}: duplicate dataset_numeric_id")
        opened.add(value)
    return opened


def prepare_industryor_interpretation(
    *,
    dataset_path: Path,
    opened_manifest_path: Path,
    output_dir: Path,
    dataset_commit: str,
    seed: str,
    per_difficulty: int = 8,
) -> dict[str, Any]:
    if per_difficulty <= 0:
        raise InterpretationAuditError("per_difficulty must be positive")
    rows = _load_industryor(dataset_path)
    opened = _opened_numeric_ids(opened_manifest_path)
    by_difficulty: dict[str, list[dict[str, Any]]] = {difficulty: [] for difficulty in DIFFICULTIES}
    for row in rows:
        if row["id"] not in opened:
            by_difficulty[row["difficulty"]].append(row)
    selected: list[dict[str, Any]] = []
    available: dict[str, int] = {}
    for difficulty in DIFFICULTIES:
        candidates = by_difficulty[difficulty]
        available[difficulty] = len(candidates)
        if len(candidates) < per_difficulty:
            raise InterpretationAuditError(
                f"IndustryOR {difficulty} has {len(candidates)} unopened rows; requires {per_difficulty}"
            )
        ranked = sorted(candidates, key=lambda row: sha256_text(f"{seed}:{_row_id(row['id'])}"))
        selected.extend(ranked[:per_difficulty])
    source_manifest: list[dict[str, Any]] = []
    hidden: list[dict[str, Any]] = []
    selection: list[dict[str, Any]] = []
    for row in selected:
        value = row["id"]
        row_id = _row_id(value)
        statement = _statement_text(row, dataset_id=value)
        statement_path = output_dir / "source" / "statements" / f"{_dataset_id(value)}.txt"
        if statement_path.exists():
            raise InterpretationAuditError(f"refusing to overwrite frozen statement: {statement_path}")
        statement_path.parent.mkdir(parents=True, exist_ok=True)
        statement_path.write_text(statement, encoding="utf-8")
        relative_statement = statement_path.relative_to(output_dir)
        source_manifest.append(
            {
                "row_id": row_id,
                "split": f"industryor_{str(row['difficulty']).lower()}",
                "statement_path": str(relative_statement),
                "source_sha256": sha256_text(statement),
            }
        )
        hidden.append(
            {
                "row_id": row_id,
                "dataset_id": _dataset_id(value),
                "dataset_numeric_id": value,
                "difficulty": row["difficulty"],
                "reference_answer": row["en_answer"],
            }
        )
        selection.append(
            {
                "row_id": row_id,
                "dataset_id": _dataset_id(value),
                "difficulty": row["difficulty"],
                "rank_sha256": sha256_text(f"{seed}:{row_id}"),
            }
        )
    write_jsonl(output_dir / "source" / "evidence-source-manifest.jsonl", source_manifest)
    write_jsonl(output_dir / "hidden" / "answer-key.jsonl", hidden)
    write_jsonl(output_dir / "provenance" / "selection.jsonl", selection)
    provenance = {
        "schema_version": "industryor_interpretation_provenance_v1",
        "dataset": {
            "name": "IndustryOR",
            "path": str(dataset_path.resolve()),
            "sha256": sha256_file(dataset_path),
            "commit": dataset_commit,
            "rows": len(rows),
        },
        "opened_manifest": {
            "path": str(opened_manifest_path.resolve()),
            "sha256": sha256_file(opened_manifest_path),
            "opened_rows": len(opened),
            "freshness_definition": "no recorded prior nested-Codex event path for the dataset row",
        },
        "selection": {
            "seed": seed,
            "algorithm": "SHA256(seed:row_id), first N within each declared difficulty",
            "per_difficulty": per_difficulty,
            "selected_rows": len(selected),
            "available_unopened_by_difficulty": available,
        },
        "answer_policy": INDUSTRYOR_ANSWER_POLICY.to_dict(),
        "answer_access": {
            "generation": "forbidden",
            "adjudication": "forbidden",
            "post_termination_comparison": "evaluator_only",
        },
        "paths": {
            "source_manifest": "source/evidence-source-manifest.jsonl",
            "hidden_answers": "hidden/answer-key.jsonl",
            "selection": "provenance/selection.jsonl",
        },
    }
    write_json(output_dir / "provenance" / "provenance.json", provenance)
    return {
        "selected": len(selected),
        "opened": len(opened),
        "available_unopened_by_difficulty": available,
    }


def _run_rows(run_dir: Path) -> list[Path]:
    row_root = run_dir / "rows"
    if not row_root.is_dir():
        raise InterpretationAuditError(f"run has no rows directory: {run_dir}")
    return sorted(path for path in row_root.iterdir() if path.is_dir())


def evaluate_interpretation_run(
    *,
    run_dir: Path,
    output_path: Path,
    expected_rows: int,
    min_valid: int,
    min_material_multi_variant: int,
) -> dict[str, Any]:
    workspaces = _run_rows(run_dir)
    rows: list[dict[str, Any]] = []
    for workspace in workspaces:
        manifest_path = workspace / "run-manifest.json"
        validated_path = workspace / "validated-interpretation-set.json"
        if not manifest_path.is_file():
            rows.append({"row_id": workspace.name, "terminal_status": "missing_manifest", "valid": False})
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        validated = json.loads(validated_path.read_text(encoding="utf-8")) if validated_path.is_file() else {}
        rows.append(
            {
                "row_id": workspace.name,
                "terminal_status": manifest.get("terminal_status", "unknown"),
                "valid": manifest.get("terminal_status") == "success" and bool(validated),
                "material_multi_variant": bool(validated.get("material_multi_variant")),
                "leakage_findings": manifest.get("leakage_findings", []),
            }
        )
    terminal = sum(row["terminal_status"] in TERMINAL_STATES for row in rows)
    valid = sum(row["valid"] for row in rows)
    material = sum(row.get("material_multi_variant", False) for row in rows)
    leakage = sum(bool(row.get("leakage_findings")) for row in rows)
    passed = (
        len(rows) == expected_rows
        and terminal == expected_rows
        and valid >= min_valid
        and material >= min_material_multi_variant
        and leakage == 0
    )
    result = {
        "schema_version": "interpretation_development_gate_v1",
        "status": "pass" if passed else "fail",
        "authorized_next_wave": passed,
        "expected_rows": expected_rows,
        "observed_rows": len(rows),
        "terminal_rows": terminal,
        "valid_rows": valid,
        "material_multi_variant_rows": material,
        "leakage_rows": leakage,
        "requirements": {
            "min_valid": min_valid,
            "min_material_multi_variant": min_material_multi_variant,
            "max_leakage": 0,
        },
        "rows": rows,
    }
    write_json(output_path, result)
    return result


def _manifest(workspace: Path) -> dict[str, Any] | None:
    path = workspace / "run-manifest.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def _results_agree(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if canonical_solver_status(left.get("status")) != canonical_solver_status(right.get("status")):
        return False
    left_obj = left.get("objective")
    right_obj = right.get("objective")
    if left_obj is None or right_obj is None:
        return left_obj == right_obj
    if not isinstance(left_obj, (int, float)) or not isinstance(right_obj, (int, float)):
        return False
    return math.isclose(
        float(left_obj),
        float(right_obj),
        rel_tol=INDUSTRYOR_ANSWER_POLICY.solver_relative_tolerance,
        abs_tol=INDUSTRYOR_ANSWER_POLICY.solver_absolute_tolerance,
    )


def _category(results: list[dict[str, Any]], answer: Any, *, complete: bool = True) -> str:
    if not complete or not results:
        return "unresolved"
    matches = [result_matches_answer(result, answer, policy=INDUSTRYOR_ANSWER_POLICY) for result in results]
    if all(matches):
        return "robustly_supported"
    if any(matches):
        return "partially_supported"
    return "unsupported_within_enumerated_set"


def _baseline_result(workspace: Path, answer: Any) -> dict[str, Any]:
    manifest = _manifest(workspace)
    result = {
        "terminal_status": manifest.get("terminal_status", "not_run") if manifest else "not_run",
        "valid": False,
        "support_category": "unresolved",
        "chosen_domain": "unresolved",
        "source_status": "unresolved",
        "leakage": bool(manifest and manifest.get("leakage_findings")),
    }
    if not manifest or manifest.get("terminal_status") != "success":
        return result
    report_path = workspace / "parent_solver_report.json"
    audit_path = workspace / "audit.json"
    if not report_path.is_file() or not audit_path.is_file():
        return result
    report = json.loads(report_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    chosen = audit.get("chosen_domain", "unresolved")
    domains = [chosen] if chosen in {"continuous", "integer"} else ["continuous", "integer"] if chosen == "both" else []
    selected = [report.get(domain, {}) for domain in domains]
    complete = bool(selected) and all(isinstance(item, dict) for item in selected)
    if len(selected) == 2 and not _results_agree(selected[0], selected[1]):
        complete = False
    result.update(
        {
            "valid": True,
            "support_category": _category(selected, answer, complete=complete),
            "chosen_domain": chosen,
            "source_status": audit.get("source_status", "unresolved"),
        }
    )
    return result


def _candidate_result(workspace: Path, answer: Any) -> dict[str, Any]:
    manifest = _manifest(workspace)
    result = {
        "terminal_status": manifest.get("terminal_status", "not_run") if manifest else "not_run",
        "valid": False,
        "support_category": "unresolved",
        "enumeration_status": "missing",
        "variant_count": 0,
        "material_multi_variant": False,
        "variants": [],
        "leakage": bool(manifest and manifest.get("leakage_findings")),
    }
    validated_path = workspace / "validated-interpretation-set.json"
    if not manifest or manifest.get("terminal_status") != "success" or not validated_path.is_file():
        return result
    validated = json.loads(validated_path.read_text(encoding="utf-8"))
    variants = validated.get("variants", [])
    results = [variant["selected_result"] for variant in variants if isinstance(variant.get("selected_result"), dict)]
    complete = validated.get("enumeration_status") == "within_cap" and len(results) == len(variants) and bool(variants)
    result.update(
        {
            "valid": True,
            "support_category": _category(results, answer, complete=complete),
            "enumeration_status": validated.get("enumeration_status", "missing"),
            "variant_count": len(variants),
            "material_multi_variant": bool(validated.get("material_multi_variant")),
            "variants": variants,
        }
    )
    return result


def compare_industryor_runs(
    *,
    campaign_dir: Path,
    baseline_run_dir: Path,
    candidate_run_dir: Path,
) -> dict[str, Any]:
    source_rows = read_jsonl(campaign_dir / "source" / "evidence-source-manifest.jsonl")
    hidden = {row["row_id"]: row for row in read_jsonl(campaign_dir / "hidden" / "answer-key.jsonl")}
    comparison: list[dict[str, Any]] = []
    for source_row in source_rows:
        row_id = source_row["row_id"]
        answer_row = hidden.get(row_id)
        if answer_row is None:
            raise InterpretationAuditError(f"hidden answer missing for {row_id}")
        baseline = _baseline_result(baseline_run_dir / "rows" / row_id, answer_row["reference_answer"])
        candidate = _candidate_result(candidate_run_dir / "rows" / row_id, answer_row["reference_answer"])
        comparison.append(
            {
                "row_id": row_id,
                "dataset_id": answer_row["dataset_id"],
                "difficulty": answer_row["difficulty"],
                "reference_answer": answer_row["reference_answer"],
                "baseline_terminal_status": baseline["terminal_status"],
                "candidate_terminal_status": candidate["terminal_status"],
                "paired_valid": baseline["valid"] and candidate["valid"],
                "baseline_support_category": baseline["support_category"],
                "candidate_support_category": candidate["support_category"],
                "baseline_chosen_domain": baseline["chosen_domain"],
                "baseline_source_status": baseline["source_status"],
                "candidate_enumeration_status": candidate["enumeration_status"],
                "candidate_variant_count": candidate["variant_count"],
                "material_multi_variant": candidate["material_multi_variant"],
                "support_category_changed": baseline["support_category"] != candidate["support_category"],
                "leakage": baseline["leakage"] or candidate["leakage"],
                "candidate_variants": candidate["variants"],
            }
        )
    declared = len(source_rows)
    baseline_terminal = sum(row["baseline_terminal_status"] in TERMINAL_STATES for row in comparison)
    candidate_terminal = sum(row["candidate_terminal_status"] in TERMINAL_STATES for row in comparison)
    paired_valid = sum(row["paired_valid"] for row in comparison)
    leakage = sum(row["leakage"] for row in comparison)
    main_gate = (
        declared == 24
        and baseline_terminal == declared
        and candidate_terminal == declared
        and paired_valid >= 22
        and leakage == 0
    )
    summary = {
        "schema_version": "industryor_answer_support_comparison_v1",
        "declared_rows": declared,
        "baseline_terminal_rows": baseline_terminal,
        "candidate_terminal_rows": candidate_terminal,
        "paired_valid_rows": paired_valid,
        "leakage_rows": leakage,
        "material_multi_variant_rows": sum(row["material_multi_variant"] for row in comparison),
        "baseline_categories": {
            category: sum(row["baseline_support_category"] == category for row in comparison)
            for category in sorted(SUPPORT_CATEGORIES)
        },
        "candidate_categories": {
            category: sum(row["candidate_support_category"] == category for row in comparison)
            for category in sorted(SUPPORT_CATEGORIES)
        },
        "support_category_changes": sum(row["support_category_changed"] for row in comparison),
        "main_gate_pass": main_gate,
        "sol_authorized": main_gate,
        "requirements": {
            "declared_rows": 24,
            "terminal_rows_per_arm": 24,
            "min_paired_valid": 22,
            "max_leakage": 0,
        },
    }
    write_jsonl(campaign_dir / "comparisons" / "terra-answer-support.jsonl", comparison)
    write_json(campaign_dir / "comparisons" / "terra-answer-support-summary.json", summary)
    return summary


def _recursive_forbidden_keys(payload: Any, path: str = "packet") -> list[str]:
    forbidden = ("answer", "baseline", "historical", "corrected", "reference")
    findings: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            child = f"{path}.{key}"
            if any(marker in key.lower() for marker in forbidden):
                findings.append(child)
            findings.extend(_recursive_forbidden_keys(value, child))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            findings.extend(_recursive_forbidden_keys(value, f"{path}[{index}]"))
    return findings


def _packet(candidate_workspace: Path, row_id: str, source_sha256: str) -> dict[str, Any]:
    validated = json.loads((candidate_workspace / "validated-interpretation-set.json").read_text(encoding="utf-8"))
    variants: list[dict[str, Any]] = []
    for variant in validated["variants"]:
        variant_id = variant["variant_id"]
        variant_dir = candidate_workspace / "variants" / variant_id
        variants.append(
            {
                "variant_id": variant_id,
                "domain": variant["domain"],
                "changed_assumption": variant["changed_assumption"],
                "material": variant["material"],
                "source_quotes": variant["source_quotes"],
                "model_ir_fingerprint": variant["model_ir_fingerprint"],
                "problem": json.loads((variant_dir / "problem.json").read_text(encoding="utf-8")),
                "parent_solver_result": variant["selected_result"],
                "parent_model_ir": json.loads((variant_dir / "parent_model_ir.json").read_text(encoding="utf-8"))[
                    variant["domain"]
                ],
            }
        )
    packet = {
        "schema_version": "interpretation_adjudication_packet_v1",
        "row_id": row_id,
        "source_sha256": source_sha256,
        "enumeration_status": validated["enumeration_status"],
        "variants": variants,
    }
    findings = _recursive_forbidden_keys(packet)
    if findings:
        raise InterpretationAuditError(f"adjudication packet contains forbidden keys: {findings}")
    return packet


def select_interpretation_adjudication(
    *,
    campaign_dir: Path,
    candidate_run_dir: Path,
    seed: str,
    disputed_count: int = 8,
    robust_control_count: int = 4,
) -> dict[str, Any]:
    summary = json.loads((campaign_dir / "comparisons" / "terra-answer-support-summary.json").read_text(encoding="utf-8"))
    if not summary.get("sol_authorized"):
        result = {"status": "blocked", "reason": "main_terra_gate_failed", "selected_total": 0}
        write_json(campaign_dir / "provenance" / "sol-selection.json", result)
        return result
    rows = read_jsonl(campaign_dir / "comparisons" / "terra-answer-support.jsonl")
    source = {row["row_id"]: row for row in read_jsonl(campaign_dir / "source" / "evidence-source-manifest.jsonl")}

    def rank(row: dict[str, Any], group: str) -> str:
        return sha256_text(f"{seed}:{group}:{row['row_id']}")

    def disputed_priority(row: dict[str, Any]) -> tuple[int, str]:
        category = row["candidate_support_category"]
        if category in {"unsupported_within_enumerated_set", "unresolved"}:
            priority = 0
        elif row["material_multi_variant"]:
            priority = 1
        elif row["support_category_changed"]:
            priority = 2
        else:
            priority = 3
        return priority, rank(row, "disputed")

    disputed_pool = [
        row
        for row in rows
        if row["paired_valid"]
        and (
            row["candidate_support_category"] != "robustly_supported"
            or row["material_multi_variant"]
            or row["support_category_changed"]
        )
    ]
    disputed = sorted(disputed_pool, key=disputed_priority)[:disputed_count]
    selected_ids = {row["row_id"] for row in disputed}
    robust_pool = [
        row
        for row in rows
        if row["paired_valid"]
        and row["candidate_support_category"] == "robustly_supported"
        and row["row_id"] not in selected_ids
    ]
    robust = sorted(robust_pool, key=lambda row: rank(row, "robust-control"))[:robust_control_count]
    if len(robust) < robust_control_count:
        result = {
            "status": "blocked",
            "reason": "insufficient_robust_controls",
            "required_robust_controls": robust_control_count,
            "available_robust_controls": len(robust),
            "selected_total": 0,
        }
        write_json(campaign_dir / "provenance" / "sol-selection.json", result)
        return result
    selected_ids.update(row["row_id"] for row in robust)
    screening_pool = [
        row for row in rows if row["paired_valid"] and row["row_id"] not in selected_ids
    ]
    screening = sorted(screening_pool, key=lambda row: rank(row, "signal-screen"))[
        : max(0, disputed_count - len(disputed))
    ]
    if len(disputed) + len(screening) < disputed_count:
        result = {
            "status": "blocked",
            "reason": "insufficient_rows_for_sol_sample",
            "required_non_control_rows": disputed_count,
            "available_non_control_rows": len(disputed) + len(screening),
            "selected_total": 0,
        }
        write_json(campaign_dir / "provenance" / "sol-selection.json", result)
        return result
    manifest: list[dict[str, Any]] = []
    selection_rows: list[dict[str, Any]] = []
    for group, selected in (
        ("disputed", disputed),
        ("signal_screen", screening),
        ("robust_control", robust),
    ):
        for row in selected:
            row_id = row["row_id"]
            source_row = source[row_id]
            packet = _packet(candidate_run_dir / "rows" / row_id, row_id, source_row["source_sha256"])
            packet_path = campaign_dir / "source" / "sol-packets" / f"{row_id}.json"
            write_json(packet_path, packet)
            manifest.append(
                {
                    "row_id": row_id,
                    "split": f"sol_{group}",
                    "statement_path": source_row["statement_path"],
                    "source_sha256": source_row["source_sha256"],
                    "packet_path": str(packet_path.relative_to(campaign_dir)),
                    "packet_sha256": sha256_file(packet_path),
                }
            )
            selection_rows.append({"row_id": row_id, "selection_group": group})
    write_jsonl(campaign_dir / "source" / "sol-interpretation-manifest.jsonl", manifest)
    result = {
        "schema_version": "industryor_sol_selection_v1",
        "status": "frozen",
        "seed": seed,
        "selected_disputed": len(disputed),
        "selected_signal_screens": len(screening),
        "selected_robust_controls": len(robust),
        "selected_total": len(manifest),
        "selection": selection_rows,
        "answer_access": "forbidden",
        "manifest": "source/sol-interpretation-manifest.jsonl",
    }
    write_json(campaign_dir / "provenance" / "sol-selection.json", result)
    return result


def _post_sol_category(
    *,
    packet: dict[str, Any],
    adjudication: dict[str, Any],
    answer: Any,
) -> tuple[str, list[dict[str, Any]]]:
    review = {row["variant_id"]: row for row in adjudication["variants"]}
    retained = [
        variant
        for variant in packet["variants"]
        if review[variant["variant_id"]]["support_status"] != "contradicted"
    ]
    complete = packet.get("enumeration_status") == "within_cap" and not adjudication.get("obvious_omission")
    return _category([variant["parent_solver_result"] for variant in retained], answer, complete=complete), retained


def _material_after_sol(retained: list[dict[str, Any]], adjudication: dict[str, Any]) -> bool:
    review = {row["variant_id"]: row for row in adjudication["variants"]}
    material = [
        variant
        for variant in retained
        if variant["material"] and review[variant["variant_id"]]["material"]
    ]
    fingerprints = {variant["model_ir_fingerprint"] for variant in material}
    outcomes = {
        (
            canonical_solver_status(variant["parent_solver_result"].get("status")),
            variant["parent_solver_result"].get("objective"),
        )
        for variant in material
    }
    return len(fingerprints) >= 2 and len(outcomes) >= 2


def finalize_industryor_interpretation(
    *,
    campaign_dir: Path,
    sol_run_dir: Path,
) -> dict[str, Any]:
    comparison = {row["row_id"]: row for row in read_jsonl(campaign_dir / "comparisons" / "terra-answer-support.jsonl")}
    hidden = {row["row_id"]: row for row in read_jsonl(campaign_dir / "hidden" / "answer-key.jsonl")}
    sol_manifest = read_jsonl(campaign_dir / "source" / "sol-interpretation-manifest.jsonl")
    selection = json.loads((campaign_dir / "provenance" / "sol-selection.json").read_text(encoding="utf-8"))
    selection_groups = {row["row_id"]: row["selection_group"] for row in selection["selection"]}
    rows: list[dict[str, Any]] = []
    for manifest_row in sol_manifest:
        row_id = manifest_row["row_id"]
        workspace = sol_run_dir / "rows" / row_id
        run_manifest = _manifest(workspace)
        valid = bool(run_manifest and run_manifest.get("terminal_status") == "success")
        pre_category = comparison[row_id]["candidate_support_category"]
        post_category = "unresolved"
        material_after = False
        obvious_omission = None
        if valid:
            packet = json.loads((campaign_dir / manifest_row["packet_path"]).read_text(encoding="utf-8"))
            adjudication = json.loads((workspace / "adjudication.json").read_text(encoding="utf-8"))
            post_category, retained = _post_sol_category(
                packet=packet,
                adjudication=adjudication,
                answer=hidden[row_id]["reference_answer"],
            )
            material_after = _material_after_sol(retained, adjudication)
            obvious_omission = adjudication.get("obvious_omission")
        rows.append(
            {
                "row_id": row_id,
                "selection_group": selection_groups[row_id],
                "sol_terminal_status": run_manifest.get("terminal_status", "not_run") if run_manifest else "not_run",
                "sol_valid": valid,
                "pre_sol_support_category": pre_category,
                "post_sol_support_category": post_category,
                "category_stable": valid and pre_category == post_category,
                "material_multi_variant_after_sol": valid and material_after,
                "obvious_omission": obvious_omission,
            }
        )
    terminal = sum(row["sol_terminal_status"] in TERMINAL_STATES for row in rows)
    valid_rows = [row for row in rows if row["sol_valid"]]
    agreement = sum(row["category_stable"] for row in valid_rows)
    agreement_rate = agreement / len(valid_rows) if valid_rows else 0.0
    robust_shifts = sum(
        row["selection_group"] == "robust_control"
        and row["post_sol_support_category"] in {"unsupported_within_enumerated_set", "unresolved"}
        for row in valid_rows
    )
    material_cases = sum(row["material_multi_variant_after_sol"] for row in valid_rows)
    execution_pass = terminal == len(sol_manifest) and len(valid_rows) >= 10
    stability_pass = agreement_rate >= 0.8 and robust_shifts <= 1
    signal_pass = material_cases >= 3
    if not execution_pass or not stability_pass:
        verdict = "park_interpretation_uncertainty_route"
        next_route = "stop_or_redesign_without_reusing_industryor"
    elif not signal_pass:
        verdict = "bounded_negative_insufficient_fresh_signal"
        next_route = "park_external_replication"
    else:
        verdict = "continue_to_external_confirmatory_campaign"
        next_route = "acquire_new_external_denominator"
    summary = {
        "schema_version": "industryor_interpretation_final_gate_v1",
        "verdict": verdict,
        "next_route": next_route,
        "paper_writing_allowed": False,
        "sol_declared_rows": len(sol_manifest),
        "sol_terminal_rows": terminal,
        "sol_valid_rows": len(valid_rows),
        "category_agreement": agreement,
        "category_agreement_rate": agreement_rate,
        "robust_control_shifts": robust_shifts,
        "material_multi_variant_rows_after_sol": material_cases,
        "execution_pass": execution_pass,
        "stability_pass": stability_pass,
        "signal_pass": signal_pass,
        "requirements": {
            "min_sol_valid": 10,
            "min_category_agreement_rate": 0.8,
            "max_robust_control_shifts": 1,
            "min_material_multi_variant_rows": 3,
        },
    }
    write_jsonl(campaign_dir / "comparisons" / "sol-adjudicated-answer-support.jsonl", rows)
    write_json(campaign_dir / "comparisons" / "final-gate-summary.json", summary)
    write_json(
        campaign_dir / "route_decision.json",
        {
            "decision_id": "D-industryor-interpretation-set-v0",
            **summary,
            "claims_not_made": [
                "benchmark answer errors",
                "fault prevalence",
                "model adjudication as ground truth",
                "paper readiness",
            ],
        },
    )
    return summary
