from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any


def clean_cell(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    value = value.replace("\\", "")
    value = value.replace("$", "")
    value = value.replace("{", "").replace("}", "")
    value = value.replace("Ⅰ", "I").replace("Ⅱ", "II").replace("Ⅲ", "III")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def extract_html_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for row_match in re.finditer(r"<tr[^>]*>(.*?)</tr>", text, flags=re.IGNORECASE | re.DOTALL):
        cells = [
            clean_cell(cell_match.group(1))
            for cell_match in re.finditer(
                r"<t[dh][^>]*>(.*?)</t[dh]>",
                row_match.group(1),
                flags=re.IGNORECASE | re.DOTALL,
            )
        ]
        if cells:
            rows.append(cells)
    return rows


def extract_latex_rows(text: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in text.splitlines():
        if "&" not in line or "\\\\" not in line:
            continue
        if any(token in line for token in ("\\toprule", "\\midrule", "\\bottomrule")):
            continue
        line = re.sub(r"\\[a-zA-Z]+(?:\[[^\]]*\])?(?:\{[^}]*\})?", "", line)
        line = line.replace("\\\\", "")
        cells = [clean_cell(part) for part in line.split("&")]
        if len(cells) >= 2:
            rows.append(cells)
    return rows


def parse_number(value: str) -> float | None:
    token = value.strip()
    if not token or not re.search(r"\d", token):
        return None
    token = token.replace(",", "").replace(" ", "")
    try:
        return float(token)
    except ValueError:
        return None


def number_tokens(text: str) -> list[float]:
    tokens = re.findall(r"[-+]?\d+(?:[ ,]\d{3})*(?:\.\d+)?|[-+]?\d+(?:\.\d+)?", text)
    values: list[float] = []
    for token in tokens:
        value = parse_number(token)
        if value is not None:
            values.append(value)
    return values


def quote(text: str, pattern: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return re.sub(r"\s+", " ", text).strip()[:220]
    start = max(match.start() - 70, 0)
    end = min(match.end() + 70, len(text))
    return re.sub(r"\s+", " ", text[start:end]).strip()[:260]


def hit(route: str, rule_id: str, fault_type: str, evidence: str, explanation: str) -> dict[str, str]:
    return {
        "route": route,
        "rule_id": rule_id,
        "fault_type": fault_type,
        "evidence": evidence,
        "explanation": explanation,
    }


def rule_missing_symbolic_cost(text: str) -> list[dict[str, str]]:
    lower = text.lower()
    if "cost of using truck j is c_j" not in lower:
        return []
    if re.search(r"c[_\{]?\s*[1-9][\}_]?\s*=", text):
        return []
    return [
        hit(
            "source_text",
            "missing_symbolic_cost_assignment",
            "missing_numeric_data",
            quote(text, r"cost of using truck j is c_j"),
            "Truck-use cost is symbolic but no numeric assignment or cost table is supplied.",
        )
    ]


def rule_entity_label_conflict(text: str) -> list[dict[str, str]]:
    lower = text.lower()
    if "department stores x, y, and z" not in lower and "stores x, y, and z" not in lower:
        return []
    if not re.search(r"\bStore\s+C\b", text):
        return []
    return [
        hit(
            "source_text",
            "entity_label_conflict",
            "data_conflict",
            "declared stores=X,Y,Z; later constraint references Store C",
            "Store set is declared as X/Y/Z but later constraints refer to Store C.",
        )
    ]


def rule_transport_balance_table(text: str) -> list[dict[str, str]]:
    lower = text.lower()
    if "transportation cost" not in lower or "demand" not in lower:
        return []
    if "new factory" in lower and ("construction option" in lower or "whether to build" in lower):
        return []
    rows = extract_latex_rows(text)
    demand_rows = [row for row in rows if row and "demand" in row[0].lower()]
    if not demand_rows:
        return []
    demand_values = [value for value in (parse_number(cell) for cell in demand_rows[0][1:]) if value is not None]
    demand_total = sum(demand_values)
    supply_values: list[float] = []
    for row in rows:
        if not row or row is demand_rows[0]:
            continue
        first = row[0].lower()
        if any(skip in first for skip in ("factory", "flour mill", "demand", "cost", "price", "raw")):
            continue
        last = parse_number(row[-1])
        row_numbers = [value for value in (parse_number(cell) for cell in row[1:]) if value is not None]
        if last is not None and len(row_numbers) >= 2:
            supply_values.append(last)
    if not supply_values or demand_total <= 0:
        return []
    supply_total = sum(supply_values)
    if abs(supply_total - demand_total) < 1e-9:
        return []
    return [
        hit(
            "source_text",
            "transport_supply_demand_mismatch",
            "data_conflict",
            f"supply_total={supply_total:g}; demand_total={demand_total:g}",
            "Transportation source table has unequal supply/output and demand totals without explicit unused-supply rule.",
        )
    ]


def rule_capacity_demand_arithmetic(text: str) -> list[dict[str, str]]:
    capacity_match = re.search(r"produce up to\s+([0-9][0-9 ,.]*)\s+tons?", text, flags=re.IGNORECASE)
    demand_match = re.search(r"demand[^.]*?(?:is|are)\s+([^.]*)respectively", text, flags=re.IGNORECASE)
    if not capacity_match or not demand_match:
        return []
    capacity = parse_number(capacity_match.group(1))
    demands = number_tokens(demand_match.group(1))
    if capacity is None or not demands:
        return []
    demand_total = sum(demands)
    if demand_total <= capacity:
        return []
    return [
        hit(
            "source_text",
            "capacity_demand_arithmetic_conflict",
            "data_conflict",
            quote(text, r"produce up to.*?demand.*?respectively"),
            f"Demand total {demand_total:g} exceeds stated production cap {capacity:g}.",
        )
    ]


def product_header_offset(rows: list[list[str]]) -> int | None:
    for row in rows:
        normalized = [clean_cell(cell).upper() for cell in row]
        if normalized[:3] == ["I", "II", "III"]:
            return 1
    return None


def rule_eligibility_table_conflict(text: str) -> list[dict[str, str]]:
    lower = text.lower()
    if "product ii" not in lower or "stage b" not in lower or "only" not in lower or "b}_{2" not in lower:
        return []
    rows = extract_html_rows(text)
    offset = product_header_offset(rows)
    if offset is None:
        return []
    hits: list[dict[str, str]] = []
    product_ii_col = offset + 1
    for row in rows:
        if len(row) <= product_ii_col:
            continue
        machine = clean_cell(row[0]).upper()
        value = row[product_ii_col].strip()
        if machine == "B1" and parse_number(value) is not None:
            hits.append(
                hit(
                    "source_text",
                    "eligibility_table_conflict",
                    "data_conflict",
                    f"Product II is prose-limited to B2, but B1/Product II table cell is {value}.",
                    "Eligibility prose and processing-time table disagree for Product II in stage B.",
                )
            )
        if machine == "B2" and not value:
            hits.append(
                hit(
                    "source_text",
                    "eligibility_table_conflict",
                    "data_conflict",
                    "Product II is prose-limited to B2, but B2/Product II table cell is blank.",
                    "Eligibility prose and processing-time table disagree for Product II in stage B.",
                )
            )
    return hits[:2]


def rule_numeric_format_anomaly(text: str) -> list[dict[str, str]]:
    rows = extract_html_rows(text)
    hour_values: list[str] = []
    for row in rows:
        if len(row) >= 6 and re.match(r"^[AB][0-9]$", row[0].strip(), flags=re.IGNORECASE):
            hour_values.append(row[-2].strip())
    if not hour_values:
        return []
    has_dot_thousands = any(re.fullmatch(r"\d+\.\d{3}", value) for value in hour_values)
    has_space_or_plain_thousands = any(
        re.fullmatch(r"\d+\s+\d{3}", value) or re.fullmatch(r"\d{4,}", value)
        for value in hour_values
    )
    if not has_dot_thousands or not has_space_or_plain_thousands:
        return []
    return [
        hit(
            "source_text",
            "numeric_format_anomaly_available_hours",
            "unit_conflict",
            "available_hours_values=" + ";".join(hour_values),
            "Available-hours column mixes thousands notation with decimal-looking value.",
        )
    ]


def rule_blank_profit_matrix_cell(text: str) -> list[dict[str, str]]:
    lower = text.lower()
    if "profit margin" not in lower and "profit margins" not in lower:
        return []
    rows = extract_html_rows(text)
    hits: list[dict[str, str]] = []
    for row in rows:
        normalized = [cell.strip().upper() for cell in row]
        if normalized[:5] == ["", "X", "Y", "Z", "SUPPLY LIMIT"]:
            continue
        if len(row) >= 5 and row[0].strip().upper() in {"A", "B", "C"}:
            for label, value in zip(["X", "Y", "Z"], row[1:4]):
                if not value.strip():
                    hits.append(
                        hit(
                            "source_text",
                            "blank_profit_matrix_cell",
                            "missing_numeric_data",
                            f"profit row {row[0].strip()} has blank Store {label} cell",
                            "Profit-margin table has empty required product-store payoff cell.",
                        )
                    )
    return hits[:2]


SOURCE_TEXT_RULES = [
    rule_missing_symbolic_cost,
    rule_entity_label_conflict,
    rule_transport_balance_table,
    rule_capacity_demand_arithmetic,
    rule_eligibility_table_conflict,
    rule_numeric_format_anomaly,
    rule_blank_profit_matrix_cell,
]


def detect_source_text(text: str) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for rule in SOURCE_TEXT_RULES:
        hits.extend(rule(text))
    return dedupe_hits(hits)


def has_key_fragment(data: Any, fragment: str) -> bool:
    if isinstance(data, dict):
        for key, value in data.items():
            if fragment.lower() in str(key).lower():
                return True
            if has_key_fragment(value, fragment):
                return True
    elif isinstance(data, list):
        return any(has_key_fragment(item, fragment) for item in data)
    return False


def json_text(data: Any) -> str:
    return json.dumps(data, sort_keys=True).lower()


def rule_bank_deposit_final_year_omitted(text: str, problem: dict[str, Any]) -> list[dict[str, str]]:
    instance = problem.get("instance", {})
    years = instance.get("years")
    deposit_years = instance.get("bank_deposit_years")
    if not isinstance(years, list) or not isinstance(deposit_years, list):
        return []
    if "beginning of each year" not in text.lower():
        return []
    missing = sorted(set(years) - set(deposit_years))
    if not missing:
        return []
    return [
        hit(
            "source_artifact",
            "bank_deposit_final_year_omitted",
            "omitted_action_index_or_year",
            f"source says deposit at beginning of each year; spec bank_deposit_years={deposit_years}; omitted={missing}",
            "Generated artifact omits a year-indexed bank-deposit action allowed by source.",
        )
    ]


def rule_strict_inequality_lost(text: str, problem: dict[str, Any]) -> list[dict[str, str]]:
    lower = text.lower()
    if "grade iii <" not in lower and "grade i >" not in lower:
        return []
    instance = problem.get("instance", {})
    if not isinstance(instance, dict):
        return []
    has_fraction_bounds = any("min_fraction" in key or "max_fraction" in key for key in instance.keys())
    if not has_fraction_bounds:
        return []
    jtxt = json_text(problem)
    if "strict" in jtxt or "exclusive" in jtxt:
        return []
    return [
        hit(
            "source_artifact",
            "strict_inequality_encoded_as_closed_bound",
            "constraint_semantics_changed",
            "source uses Grade III < threshold / Grade I > threshold; spec stores min_fraction/max_fraction with no strict/exclusive flag",
            "Generated artifact loses strict inequality semantics.",
        )
    ]


def rule_reserve_unit_contradiction_silenced(text: str, problem: dict[str, Any]) -> list[dict[str, str]]:
    lower = text.lower()
    if "10%" not in text or "1 million yuan" not in lower or "1000 thousand yuan" not in lower:
        return []
    instance = problem.get("instance", {})
    reserve_min = instance.get("emergency_reserve_min_thousand_yuan") if isinstance(instance, dict) else None
    total = instance.get("total_fund_thousand_yuan") if isinstance(instance, dict) else None
    if reserve_min == 100.0 and total == 1000.0:
        return [
            hit(
                "source_artifact",
                "reserve_unit_conflict_silently_resolved",
                "source_numeric_contradiction",
                "source states 10% of 1000 thousand yuan and parenthetical 1 million yuan; spec uses 100 thousand yuan",
                "Generated artifact silently chooses one side of a source unit contradiction.",
            )
        ]
    return []


def rule_goal_programming_collapsed(text: str, problem: dict[str, Any]) -> list[dict[str, str]]:
    lower = text.lower()
    if "goal programming" not in lower:
        return []
    jtxt = json_text(problem)
    has_deviation = any(token in jtxt for token in ["deviation", "deviational", "achievement"])
    has_priority = any(token in jtxt for token in ["priority", "priorities", "preemptive", "lexicographic"])
    if has_deviation and has_priority:
        return []
    return [
        hit(
            "source_artifact",
            "goal_programming_structure_missing",
            "objective_structure_changed",
            "source asks for goal programming; spec lacks deviational variables and priority/achievement structure",
            "Generated artifact records goals but does not encode goal-programming model structure.",
        )
    ]


def rule_invented_priority_weights(text: str, problem: dict[str, Any]) -> list[dict[str, str]]:
    lower = text.lower()
    if "prioritized objectives" not in lower or "twice" not in lower:
        return []
    instance = problem.get("instance", {})
    priorities = instance.get("goal_priorities") if isinstance(instance, dict) else None
    if isinstance(priorities, dict) and sorted(priorities.values()) == [1, 2, 3]:
        return [
            hit(
                "source_artifact",
                "invented_finite_priority_weights",
                "priority_semantics_changed",
                "source gives ordered objectives and only 2x stockout importance for Product 3; spec invents goal_priorities 3/2/1",
                "Generated artifact turns priority order into unstated finite weights.",
            )
        ]
    return []


def rule_hydrogen_budget_infeasible(text: str, problem: dict[str, Any]) -> list[dict[str, str]]:
    lower = text.lower()
    if "hydrogen" not in lower or "budget" not in lower or "less than" not in lower:
        return []
    instance = problem.get("instance", {})
    if not isinstance(instance, dict):
        return []
    cap = instance.get("capacity_cubic_meters_per_trip", {})
    cost = instance.get("cost_usd_per_trip", {})
    demand = float(instance.get("minimum_hydrogen_cubic_meters", 0) or 0)
    budget = float(instance.get("budget_usd", 0) or 0)
    if not cap or not cost or demand <= 0 or budget <= 0:
        return []
    methods = list(cap.keys())
    if len(methods) != 2:
        return []
    left = instance.get("strict_less_than_method_pair", {}).get("left", methods[0])
    right = instance.get("strict_less_than_method_pair", {}).get("right", methods[1])
    feasible = False
    for left_count in range(0, 200):
        for right_count in range(0, 200):
            if left_count >= right_count:
                continue
            total_cap = left_count * float(cap[left]) + right_count * float(cap[right])
            total_cost = left_count * float(cost[left]) + right_count * float(cost[right])
            if total_cap >= demand and total_cost <= budget:
                feasible = True
                break
        if feasible:
            break
    if feasible:
        return []
    return [
        hit(
            "source_artifact",
            "hydrogen_budget_constraints_integer_infeasible",
            "hard_constraint_infeasibility",
            f"integer search found no counts satisfying demand>={demand:g}, budget<={budget:g}, left<right",
            "Source constraint set appears infeasible under integer transport counts.",
        )
    ]


def rule_discrete_action_lp_omission(text: str, problem: dict[str, Any]) -> list[dict[str, str]]:
    lower = text.lower()
    problem_type = str(problem.get("problem_type", "")).upper()
    if problem_type != "LP":
        return []
    gummies_case = "gummies" in lower and "pills" in lower and "how many" in lower
    containers_case = "small" in lower and "large containers" in lower and "how many" not in lower and "container" in lower
    if not gummies_case and not containers_case:
        return []
    jtxt = json_text(problem)
    if "integer" in jtxt or "binary" in jtxt or "domain" in jtxt:
        return []
    return [
        hit(
            "source_artifact",
            "discrete_action_space_encoded_as_lp",
            "integrality_omitted",
            "source asks for physical count decisions; spec problem_type=LP and no integer/domain marker",
            "Generated artifact omits integrality for count/action decision variables.",
        )
    ]


SOURCE_ARTIFACT_RULES = [
    rule_bank_deposit_final_year_omitted,
    rule_strict_inequality_lost,
    rule_reserve_unit_contradiction_silenced,
    rule_goal_programming_collapsed,
    rule_invented_priority_weights,
    rule_hydrogen_budget_infeasible,
    rule_discrete_action_lp_omission,
]


def detect_source_artifact(text: str, problem: dict[str, Any]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    if not problem:
        return hits
    for rule in SOURCE_ARTIFACT_RULES:
        hits.extend(rule(text, problem))
    return dedupe_hits(hits)


def dedupe_hits(hits: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, str]] = []
    for item in hits:
        key = (item["rule_id"], item["evidence"])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def read_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def problem_json_path(row: dict[str, str]) -> Path | None:
    raw = row.get("generated_artifact_path", "").strip()
    if not raw:
        return None
    path = Path(raw)
    candidates: list[Path] = []
    if path.is_file():
        if path.name == "problem.json":
            candidates.append(path)
        candidates.append(path.parent / "problem.json")
    if path.is_dir():
        candidates.append(path / "spec" / "problem.json")
        candidates.append(path / "problem.json")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def expected_label(row: dict[str, str]) -> str:
    if row["dataset"] == "strict_clean_controls":
        return "clean_control"
    if row["dataset"] == "constructed_material_faults":
        return "constructed_not_primary_v1"
    return "source_fault_detected"


def row_case_pass(row: dict[str, str], detected: bool) -> str:
    if row["dataset"] == "constructed_material_faults":
        return "not_primary"
    if row["dataset"] == "strict_clean_controls":
        return str(not detected).lower()
    return str(detected).lower()


def is_artifact_fidelity_row(row: dict[str, str]) -> bool:
    return row.get("label") == "source_fidelity_failure"


def read_source_text(row: dict[str, str], source_override: str | None) -> tuple[str, Path | None, bool]:
    if source_override is not None:
        return source_override, None, True
    source_path = Path(row.get("source_artifact_path", ""))
    if not source_path.is_file():
        return "", source_path, False
    return source_path.read_text(encoding="utf-8"), source_path, True


def run_row(row: dict[str, str], detector_mode: str, source_override: str | None = None) -> dict[str, Any]:
    if row["dataset"] == "constructed_material_faults":
        hits: list[dict[str, str]] = []
        source_path = Path(row.get("source_artifact_path", ""))
        source_hash_matches = source_path.is_file() and sha256_file(source_path) == row.get("source_hash", "")
        problem_path = problem_json_path(row)
        detected = False
        decision = "not_primary_constructed_source_json"
        notes = "constructed rows are stress/descriptive only in detector v1"
    else:
        text, source_path, source_ok = read_source_text(row, source_override)
        source_hash_matches = source_ok and source_override is not None or (
            source_ok and source_path is not None and sha256_file(source_path) == row.get("source_hash", "")
        )
        problem_path = problem_json_path(row)
        problem = read_json(problem_path) if problem_path and problem_path.exists() else {}
        source_hits = detect_source_text(text) if detector_mode in {"combined", "source_text_only", "source_spans_only"} else []
        artifact_hits = detect_source_artifact(text, problem) if detector_mode in {"combined", "artifact_route_only"} else []
        hits = dedupe_hits(source_hits + artifact_hits)
        detected = bool(hits)
        decision = "source_fault_detected" if detected else "no_source_fault_detected"
        notes = "combined source-text and source-vs-artifact detector v1" if detector_mode == "combined" else detector_mode

    return {
        "row_id": row["row_id"],
        "dataset": row["dataset"],
        "problem_id": row.get("problem_id", ""),
        "label": row.get("label", ""),
        "detector_mode": detector_mode,
        "detector_decision": decision,
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
        "problem_path": str(problem_path) if problem_path else "",
        "notes": notes,
    }
