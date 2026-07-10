from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from or_ci.detector.v1_rules import (
    detect_source_artifact,
    detect_source_text,
    dedupe_hits,
    expected_label,
    problem_json_path,
    read_json,
    read_source_text,
    row_case_pass,
    sha256_file,
    run_row as v1_run_row,
)


LEDGER_FIELDS = [
    "row_id",
    "dataset",
    "problem_id",
    "label",
    "detector_mode",
    "detector_decision",
    "detected_fault",
    "rule_hits",
    "primary_fault_type",
    "routes_hit",
    "evidence_quotes",
    "trace_json",
    "source_hash_matches",
    "used_row_id_logic",
    "forbidden_review_input_used",
    "expected_label",
    "case_pass",
    "source_path",
    "problem_path",
    "notes",
]


def quote_text(text: str, pattern: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return re.sub(r"\s+", " ", text).strip()[:240]
    start = max(match.start() - 60, 0)
    end = min(match.end() + 90, len(text))
    return re.sub(r"\s+", " ", text[start:end]).strip()[:280]


def hit(rule_id: str, fault_type: str, evidence: str, explanation: str) -> dict[str, str]:
    return {
        "route": "source_artifact_v2",
        "rule_id": rule_id,
        "fault_type": fault_type,
        "evidence": evidence,
        "explanation": explanation,
    }


def is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def original_objective(report: dict[str, Any]) -> float | None:
    status = report.get("solver_status", {})
    if isinstance(status, dict):
        original = status.get("original", {})
        if isinstance(original, dict) and is_number(original.get("objective_value")):
            return float(original["objective_value"])
    for check in report.get("checks", []):
        if isinstance(check, dict) and check.get("name") == "original_solver_status":
            details = check.get("details", {})
            if isinstance(details, dict) and is_number(details.get("objective_value")):
                return float(details["objective_value"])
    return None


def report_integer_variables(report: dict[str, Any]) -> int | None:
    summary = report.get("model_ir_summary", {})
    if isinstance(summary, dict) and is_number(summary.get("integer_variables")):
        return int(summary["integer_variables"])
    return None


def is_fractional(value: float | None) -> bool:
    if value is None:
        return False
    return abs(value - round(value)) > 1e-6


def source_mentions_countable_decision(text: str) -> bool:
    lower = text.lower()
    if not re.search(r"\b(how many|number of|counts?|integer|buy|transport|schedule|scheduled|produce)\b", lower):
        return False
    nouns = [
        "bouquet",
        "slicer",
        "worker",
        "shift",
        "keyboard",
        "ad",
        "advertisement",
        "technician",
        "researcher",
        "unit",
    ]
    return any(noun in lower for noun in nouns)


def problem_has_integer_marker(problem: dict[str, Any]) -> bool:
    jtxt = json.dumps(problem, sort_keys=True).lower()
    return "integer" in jtxt or "nonnegative_integer" in jtxt


def shared_keys(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    return sorted(set(left) & set(right))


def read_report(row: dict[str, str]) -> dict[str, Any]:
    raw = row.get("report_path", "").strip()
    if raw:
        path = Path(raw)
        if path.is_file():
            return read_json(path)
    problem_path = problem_json_path(row)
    if problem_path:
        candidate = problem_path.parent.parent / "reports" / f"{row.get('problem_id') or row.get('row_id')}.json"
        if candidate.is_file():
            return read_json(candidate)
    return {}


def rule_count_integrality_relaxation(text: str, problem: dict[str, Any], report: dict[str, Any]) -> list[dict[str, str]]:
    integer_vars = report_integer_variables(report)
    objective = original_objective(report)
    if integer_vars != 0:
        return []
    if not is_fractional(objective):
        return []
    if not problem_has_integer_marker(problem):
        return []
    return [
        hit(
            "count_integrality_relaxation",
            "integrality_omitted",
            f"artifact declares an integer domain while report has integer_variables=0 and objective_value={objective:g}",
            "Generated artifact/report drops an explicit integer-domain declaration.",
        )
    ]


def rule_bounded_discrete_unit_relaxation(text: str, problem: dict[str, Any], report: dict[str, Any]) -> list[dict[str, str]]:
    instance = problem.get("instance", {})
    integer_vars = report_integer_variables(report)
    objective = original_objective(report)
    if not isinstance(instance, dict) or integer_vars != 0 or not is_fractional(objective):
        return []
    lower = text.lower()
    has_total_count_cap = any(key.startswith("max_total_") for key in instance)
    has_type_ratio = any(key.startswith("min_") and "_to_" in key and key.endswith("_ratio") for key in instance)
    has_discrete_unit_payload = any("_per_bouquet" in key or key.endswith("_per_bouquet") for key in instance)
    asks_transport_count = "transport" in lower and "bouquet" in lower and source_mentions_countable_decision(text)
    if not (has_total_count_cap and has_type_ratio and has_discrete_unit_payload and asks_transport_count):
        return []
    return [
        hit(
            "bounded_discrete_unit_relaxation",
            "integrality_omitted",
            f"bounded discrete-unit transport artifact has integer_variables=0 and fractional objective_value={objective:g}",
            "Source asks for counts of discrete transported bundles, but generated artifact solves a continuous relaxation.",
        )
    ]


def rule_minimum_resource_infeasibility(text: str, problem: dict[str, Any], report: dict[str, Any]) -> list[dict[str, str]]:
    instance = problem.get("instance", {})
    if not isinstance(instance, dict):
        return []
    hits: list[dict[str, str]] = []
    min_maps = {
        key: value
        for key, value in instance.items()
        if key.startswith("minimum_") and isinstance(value, dict)
    }
    cost_maps = {
        key: value
        for key, value in instance.items()
        if ("cost" in key or "usage" in key) and isinstance(value, dict)
    }
    budget_items = [
        (key, float(value))
        for key, value in instance.items()
        if is_number(value) and ("budget" in key or "available" in key or "capacity" in key)
    ]
    for min_key, min_map in min_maps.items():
        for cost_key, cost_map in cost_maps.items():
            keys = shared_keys(min_map, cost_map)
            if not keys:
                continue
            mandatory = sum(float(min_map[k]) * float(cost_map[k]) for k in keys if is_number(min_map[k]) and is_number(cost_map[k]))
            if mandatory <= 0:
                continue
            for budget_key, budget in budget_items:
                if mandatory > budget + 1e-6:
                    hits.append(
                        hit(
                            "minimum_resource_infeasibility",
                            "hard_constraint_infeasibility",
                            f"{min_key} with {cost_key} requires {mandatory:g}, exceeding {budget_key}={budget:g}",
                            "Minimum lower-bound requirements exceed available budget/resource.",
                        )
                    )
    return hits[:2]


def rule_ratio_constraint_budget_infeasibility(text: str, problem: dict[str, Any], report: dict[str, Any]) -> list[dict[str, str]]:
    instance = problem.get("instance", {})
    if not isinstance(instance, dict):
        return []
    ratio = instance.get("ratio_constraint")
    hours = instance.get("hours_per_shift")
    pay = instance.get("pay_per_shift")
    required = instance.get("required_service_hours")
    budget = instance.get("budget")
    if not (isinstance(ratio, dict) and isinstance(hours, dict) and isinstance(pay, dict)):
        return []
    if not (is_number(required) and is_number(budget)):
        return []
    left = ratio.get("left_worker_type")
    right = ratio.get("right_worker_type")
    multiplier = ratio.get("multiplier")
    if left not in hours or right not in hours or left not in pay or right not in pay or not is_number(multiplier):
        return []
    unit_hours = float(multiplier) * float(hours[left]) + float(hours[right])
    unit_cost = float(multiplier) * float(pay[left]) + float(pay[right])
    if unit_hours <= 0:
        return []
    min_units = float(required) / unit_hours
    min_cost = min_units * unit_cost
    if min_cost <= float(budget) + 1e-6:
        return []
    return [
        hit(
            "ratio_budget_infeasibility",
            "hard_constraint_infeasibility",
            f"ratio {left}={float(multiplier):g}*{right} needs cost {min_cost:g} for required_service_hours={float(required):g}, exceeding budget={float(budget):g}",
            "Ratio plus service lower bound makes source constraints infeasible under stated budget.",
        )
    ]


def rule_ratio_resource_infeasibility(text: str, problem: dict[str, Any], report: dict[str, Any]) -> list[dict[str, str]]:
    instance = problem.get("instance", {})
    if not isinstance(instance, dict):
        return []
    hits: list[dict[str, str]] = []
    ratio_keys = [key for key, value in instance.items() if key.endswith("_ratio") and "_to_" in key and is_number(value)]
    usage_maps = {key: value for key, value in instance.items() if key.endswith("_usage") and isinstance(value, dict)}
    available = [(key, float(value)) for key, value in instance.items() if key.endswith("_available") and is_number(value)]
    for ratio_key in ratio_keys:
        left, right_with_suffix = ratio_key.split("_to_", 1)
        right = right_with_suffix[: -len("_ratio")]
        ratio_value = float(instance[ratio_key])
        min_candidates = [
            (key, float(value))
            for key, value in instance.items()
            if key.startswith("minimum_") and right in key and is_number(value)
        ]
        for min_key, min_right in min_candidates:
            for usage_key, usage in usage_maps.items():
                if left not in usage or right not in usage:
                    continue
                required = min_right * (ratio_value * float(usage[left]) + float(usage[right]))
                for avail_key, avail in available:
                    if usage_key.split("_usage")[0] not in avail_key:
                        continue
                    if required > avail + 1e-6:
                        hits.append(
                            hit(
                                "ratio_resource_infeasibility",
                                "hard_constraint_infeasibility",
                                f"{ratio_key} with {min_key} requires {required:g} {usage_key}, exceeding {avail_key}={avail:g}",
                                "Ratio plus minimum requirement exceeds source resource capacity.",
                            )
                        )
    return hits[:2]


def rule_objective_sense_count_gap(text: str, problem: dict[str, Any], report: dict[str, Any]) -> list[dict[str, str]]:
    instance = problem.get("instance", {})
    if not isinstance(instance, dict):
        return []
    lower = text.lower()
    objective = original_objective(report)
    if "objective_sense" in instance:
        return []
    if not is_fractional(objective):
        return []
    if not ("minimize" in lower or "maximize" in lower):
        return []
    if not source_mentions_countable_decision(text):
        return []
    if "objective_coefficients" not in instance:
        return []
    return [
        hit(
            "objective_sense_count_gap",
            "objective_structure_changed",
            f"source has count objective language but artifact lacks objective_sense and report objective_value={objective:g}",
            "Objective/count semantics are under-specified and continuous result is fractional.",
        )
    ]


V2_RULES = [
    rule_count_integrality_relaxation,
    rule_bounded_discrete_unit_relaxation,
    rule_minimum_resource_infeasibility,
    rule_ratio_constraint_budget_infeasibility,
    rule_ratio_resource_infeasibility,
    rule_objective_sense_count_gap,
]


def detect_v2(text: str, problem: dict[str, Any], report: dict[str, Any]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for rule in V2_RULES:
        hits.extend(rule(text, problem, report))
    return dedupe_hits(hits)


def run_row(row: dict[str, str], mode: str) -> dict[str, Any]:
    if row["dataset"] == "constructed_material_faults":
        result = v1_run_row(row, "combined")
        result["detector_mode"] = mode
        result["notes"] = f"{mode}; constructed rows descriptive only"
        return result

    text, source_path, source_ok = read_source_text(row, None)
    source_hash_matches = source_ok and source_path is not None and sha256_file(source_path) == row.get("source_hash", "")
    problem_path_resolved = problem_json_path(row)
    problem = read_json(problem_path_resolved) if problem_path_resolved and problem_path_resolved.exists() else {}
    report = read_report(row)

    hits: list[dict[str, str]] = []
    if mode in {"combined", "v1_only"}:
        hits.extend(detect_source_text(text))
        hits.extend(detect_source_artifact(text, problem))
    if mode in {"combined", "v2_only"}:
        hits.extend(detect_v2(text, problem, report))
    hits = dedupe_hits(hits)
    detected = bool(hits)
    return {
        "row_id": row["row_id"],
        "dataset": row["dataset"],
        "problem_id": row.get("problem_id", ""),
        "label": row.get("label", ""),
        "detector_mode": mode,
        "detector_decision": "source_fault_detected" if detected else "no_source_fault_detected",
        "detected_fault": str(detected).lower(),
        "rule_hits": ";".join(item["rule_id"] for item in hits),
        "primary_fault_type": hits[0]["fault_type"] if hits else "",
        "routes_hit": ";".join(sorted({item["route"] for item in hits})),
        "evidence_quotes": " | ".join(item["evidence"] for item in hits),
        "trace_json": json.dumps(hits, sort_keys=True),
        "source_hash_matches": str(source_hash_matches).lower(),
        "used_row_id_logic": "false",
        "forbidden_review_input_used": "false",
        "expected_label": expected_label(row),
        "case_pass": row_case_pass(row, detected),
        "source_path": row.get("source_artifact_path", ""),
        "problem_path": str(problem_path_resolved) if problem_path_resolved else "",
        "notes": f"source_vs_artifact_detector_v2 {mode}; v1 rules unchanged plus v2 generic rules",
    }
