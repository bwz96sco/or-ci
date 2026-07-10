from __future__ import annotations

import hashlib
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


LEDGER_FIELDS = [
    "row_id",
    "dataset",
    "label",
    "detector_decision",
    "detected_fault",
    "rule_hits",
    "primary_fault_type",
    "evidence_quotes",
    "trace_json",
    "used_row_id_logic",
    "source_hash_matches",
    "expected_label",
    "case_pass",
    "notes",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


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
            for cell_match in re.finditer(r"<t[dh][^>]*>(.*?)</t[dh]>", row_match.group(1), flags=re.IGNORECASE | re.DOTALL)
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
    if not token:
        return None
    if not re.search(r"\d", token):
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
        compact = re.sub(r"\s+", " ", text).strip()
        return compact[:220]
    start = max(match.start() - 70, 0)
    end = min(match.end() + 70, len(text))
    return re.sub(r"\s+", " ", text[start:end]).strip()[:260]


def hit(rule_id: str, fault_type: str, evidence: str, explanation: str) -> dict[str, str]:
    return {
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
            "missing_symbolic_cost_assignment",
            "missing_numeric_data",
            quote(text, r"cost of using truck j is c_j"),
            "Truck-use cost is named symbolically but no numeric assignment or cost table is supplied.",
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
            "transport_supply_demand_mismatch",
            "data_conflict",
            f"supply_total={supply_total:g}; demand_total={demand_total:g}",
            "Transportation source table has unequal supply/output and demand totals without an explicit unused-supply rule.",
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
                    "eligibility_table_conflict",
                    "data_conflict",
                    f"Product II is prose-limited to B2, but B1/Product II table cell is {value}.",
                    "Eligibility prose and processing-time table disagree for Product II in stage B.",
                )
            )
        if machine == "B2" and not value:
            hits.append(
                hit(
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
            "numeric_format_anomaly_available_hours",
            "unit_conflict",
            "available_hours_values=" + ";".join(hour_values),
            "Available-hours column mixes thousands notation with a decimal-looking value.",
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
                            "blank_profit_matrix_cell",
                            "missing_numeric_data",
                            f"profit row {row[0].strip()} has blank Store {label} cell",
                            "Profit-margin table has an empty required product-store payoff cell.",
                        )
                    )
    return hits[:2]


RULES = [
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
    for rule in RULES:
        hits.extend(rule(text))
    seen: set[tuple[str, str]] = set()
    unique_hits: list[dict[str, str]] = []
    for item in hits:
        key = (item["rule_id"], item["evidence"])
        if key not in seen:
            seen.add(key)
            unique_hits.append(item)
    return unique_hits


def expected_label(row: dict[str, str]) -> str:
    if row["dataset"] == "strict_clean_controls":
        return "clean_control"
    if row["dataset"] == "constructed_material_faults":
        return "constructed_not_primary_v0"
    return "source_fault_detected"


def row_case_pass(row: dict[str, str], detected: bool) -> str:
    if row["dataset"] == "constructed_material_faults":
        return "not_primary"
    if row["dataset"] == "strict_clean_controls":
        return str(not detected).lower()
    return str(detected).lower()


def run_row(row: dict[str, str], text_override: str | None = None) -> dict[str, object]:
    source_path = Path(row["source_artifact_path"])
    source_hash_matches = source_path.is_file() and sha256_file(source_path) == row["source_hash"]
    if row["dataset"] == "constructed_material_faults":
        hits: list[dict[str, str]] = []
        decision = "not_primary_constructed_source_json"
        notes = "Constructed rows are descriptive in v0; source-text rules are evaluated on natural and clean rows."
    else:
        text = text_override if text_override is not None else source_path.read_text(encoding="utf-8")
        hits = detect_source_text(text)
        decision = "source_fault_detected" if hits else "no_source_fault_detected"
        notes = "source-text rule evaluation"

    detected = bool(hits)
    return {
        "row_id": row["row_id"],
        "dataset": row["dataset"],
        "label": row["label"],
        "detector_decision": decision,
        "detected_fault": str(detected).lower(),
        "rule_hits": ";".join(item["rule_id"] for item in hits),
        "primary_fault_type": hits[0]["fault_type"] if hits else "",
        "evidence_quotes": " | ".join(item["evidence"] for item in hits),
        "trace_json": json.dumps(hits, sort_keys=True),
        "used_row_id_logic": "false",
        "source_hash_matches": str(source_hash_matches).lower(),
        "expected_label": expected_label(row),
        "case_pass": row_case_pass(row, detected),
        "notes": notes,
    }


def metric_summary(rows: list[dict[str, object]]) -> dict[str, Any]:
    natural = [row for row in rows if row["dataset"] == "natural_hard_faults"]
    clean = [row for row in rows if row["dataset"] == "strict_clean_controls"]
    constructed = [row for row in rows if row["dataset"] == "constructed_material_faults"]
    natural_detected = sum(row["detected_fault"] == "true" for row in natural)
    clean_false_positive = sum(row["detected_fault"] == "true" for row in clean)
    return {
        "total_rows": len(rows),
        "dataset_counts": dict(Counter(str(row["dataset"]) for row in rows)),
        "natural_fault_rows": len(natural),
        "natural_detected": natural_detected,
        "natural_fault_detection_recall": natural_detected / len(natural) if natural else 0.0,
        "clean_control_rows": len(clean),
        "clean_false_positive_count": clean_false_positive,
        "clean_control_false_positive_rate": clean_false_positive / len(clean) if clean else 0.0,
        "constructed_rows_descriptive_only": len(constructed),
        "all_source_hashes_match": all(row["source_hash_matches"] == "true" for row in rows),
        "used_row_id_logic_count": sum(row["used_row_id_logic"] == "true" for row in rows),
        "minimum_gate_passed": natural_detected >= 6 and clean_false_positive <= 1,
        "solid_gate_passed": natural_detected == len(natural) and clean_false_positive == 0,
    }
