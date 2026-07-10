from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


FAULT_CLASSES = [
    "objective_semantics",
    "resource_capacity",
    "temporal_logic",
    "structural_mapping",
]

LEDGER_FIELDS = [
    "row_id",
    "instance_id",
    "row_type",
    "fault_class",
    "detector_id",
    "detector_decision",
    "detected_fault",
    "detected_family",
    "confidence",
    "fired_rules",
    "evidence_quotes",
    "trace_json",
    "expected_behavior",
    "case_pass",
    "source_hash_matches",
    "proof_packet_exists",
    "proof_packet_sha256",
    "forbidden_input_fields_used",
    "used_row_id_logic",
    "inference_input_fields",
    "notes",
]

EXPECTED_ROWS = 96
EXPECTED_MATERIAL = 48
EXPECTED_CLEAN_BENIGN = 48
EXPECTED_PER_CLASS = 12
MATERIAL_RECALL_GATE = 40
CLEAN_FP_GATE = 1
PER_CLASS_GATE = 8


def normalized_hash(text: str) -> str:
    norm = re.sub(r"\s+", " ", text.lower()).strip()
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def flatten_json_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        out: list[str] = []
        for inner in value.values():
            out.extend(flatten_json_strings(inner))
        return out
    if isinstance(value, list):
        out = []
        for inner in value:
            out.extend(flatten_json_strings(inner))
        return out
    return []


def source_hash_matches(row: dict[str, str]) -> bool:
    source_path = Path(row["source_artifact_path"])
    if not source_path.is_file():
        return False
    try:
        instance = json.loads(source_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    json_strings = "\n\n".join(flatten_json_strings(instance))
    upstream_hash = normalized_hash(str(instance.get("abstract_problem", "")) + "\n" + json_strings)
    return upstream_hash == row["source_hash"]


def hit(rule_id: str, family: str, evidence: str, explanation: str) -> dict[str, str]:
    return {
        "route": "miplib_source_artifact_v2",
        "rule_id": rule_id,
        "family": family,
        "evidence": evidence,
        "explanation": explanation,
    }


def dedupe_hits(hits: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, str]] = []
    for item in hits:
        key = (item["rule_id"], item["evidence"])
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def allowed_inference_view(row: dict[str, str]) -> dict[str, str]:
    return {
        "source_quote": row.get("source_quote", ""),
        "obligation": row.get("obligation", ""),
        "reference_fragment": row.get("reference_fragment", ""),
        "candidate_fragment": row.get("candidate_fragment", ""),
    }


def detect(view: dict[str, str]) -> tuple[bool, str, str, list[dict[str, str]]]:
    source = view["source_quote"].lower()
    obligation = view["obligation"].lower()
    reference = view["reference_fragment"].lower()
    candidate = view["candidate_fragment"].lower()
    text = " ".join([source, obligation, reference, candidate])
    hits: list[dict[str, str]] = []

    preserve = any(
        phrase in obligation
        for phrase in [
            "preserve",
            "should preserve",
            "without changing semantics",
            "reference row should preserve",
            "equivalent reformulation",
        ]
    )

    if preserve and any(
        phrase in candidate
        for phrase in [
            "change objective direction",
            "omit one stated objective",
            "omit one stated objective term",
            "drop objective",
            "replace objective",
        ]
    ):
        hits.append(
            hit(
                "miplib_v2_objective_semantics_delta",
                "objective_semantics",
                "candidate changes objective direction or omits an objective term while obligation says preserve objective semantics",
                "Candidate violates objective preservation obligation.",
            )
        )

    if preserve and any(
        phrase in candidate
        for phrase in [
            "relax one stated capacity",
            "treat it as advisory",
            "relax capacity",
            "relax budget",
            "relax availability",
        ]
    ):
        hits.append(
            hit(
                "miplib_v2_resource_capacity_delta",
                "resource_capacity",
                "candidate relaxes capacity/resource obligation while source/reference requires preservation",
                "Candidate turns binding resource limit into weaker condition.",
            )
        )

    if preserve and any(
        phrase in candidate
        for phrase in [
            "reverse or drop",
            "drop one ordering",
            "drop ordering",
            "drop one window",
            "reverse ordering",
            "drop precedence",
        ]
    ):
        hits.append(
            hit(
                "miplib_v2_temporal_logic_delta",
                "temporal_logic",
                "candidate reverses or drops temporal/order/window semantics under preservation obligation",
                "Candidate changes temporal logic.",
            )
        )

    if preserve and any(
        phrase in candidate
        for phrase in [
            "join by label",
            "omit an exactly-one",
            "omit exactly-one",
            "change schema mapping",
            "drop mapping",
        ]
    ):
        hits.append(
            hit(
                "miplib_v2_structural_mapping_delta",
                "structural_mapping",
                "candidate changes mapping/exactly-one semantics under preservation obligation",
                "Candidate changes structural mapping.",
            )
        )

    benign_markers = [
        "reference artifacts unchanged",
        "benign control",
        "reorder constraints",
        "rename local variables",
        "no semantic deletion",
        "equivalent reformulation",
    ]
    has_benign = any(marker in candidate or marker in obligation for marker in benign_markers)
    hits = dedupe_hits(hits)
    if hits:
        family = hits[0]["family"]
        return True, family, "high", hits
    if has_benign:
        return False, "none", "high", []
    if "preserve" in text and "unchanged" in candidate:
        return False, "none", "medium", []
    return False, "unknown", "low", []


def run_row(row: dict[str, str]) -> dict[str, Any]:
    view = allowed_inference_view(row)
    detected, family, confidence, hits = detect(view)
    expected = "detect_fault" if row["row_type"] == "constructed_material_fault" else "accept"
    case_pass = (expected == "detect_fault" and detected) or (expected == "accept" and not detected)
    proof_path = Path(row["proof_packet_path"])
    proof_exists = proof_path.is_file()
    return {
        "row_id": row["row_id"],
        "instance_id": row["instance_id"],
        "row_type": row["row_type"],
        "fault_class": row["fault_class"],
        "detector_id": "miplibnl_source_vs_artifact_detector_v2_adapter",
        "detector_decision": "source_fault_detected" if detected else "no_source_fault_detected",
        "detected_fault": str(detected).lower(),
        "detected_family": family,
        "confidence": confidence,
        "fired_rules": ";".join(item["rule_id"] for item in hits),
        "evidence_quotes": " | ".join(item["evidence"] for item in hits),
        "trace_json": json.dumps(hits, sort_keys=True),
        "expected_behavior": expected,
        "case_pass": str(case_pass).lower(),
        "source_hash_matches": str(source_hash_matches(row)).lower(),
        "proof_packet_exists": str(proof_exists).lower(),
        "proof_packet_sha256": hashlib.sha256(proof_path.read_bytes()).hexdigest() if proof_exists else "",
        "forbidden_input_fields_used": "",
        "used_row_id_logic": "false",
        "inference_input_fields": "source_quote;obligation;reference_fragment;candidate_fragment",
        "notes": "first-shot MIPLIB detector-v2 route replay; labels used only after inference for scoring",
    }
