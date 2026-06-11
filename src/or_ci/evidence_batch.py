from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from or_ci.evidence_pack import build_evidence_pack, write_evidence_pack
from or_ci.formulation_adapter import FormulationAdapterError, materialize_formulation
from or_ci.verifier import verify


SCHEMA_VERSION = "or_ci_evidence_batch_v1"

LEDGER_FIELDS = [
    "record_id",
    "row_index",
    "row_type",
    "row_status",
    "problem_id",
    "verification_status",
    "classification",
    "statement_path",
    "formulation_path",
    "problem_path",
    "submission_path",
    "evidence_pack_path",
    "error_type",
    "error_message",
]


def run_evidence_batch(
    manifest_path: str | Path,
    out_dir: str | Path,
    *,
    manual_constraints_path: str | Path | None = None,
) -> dict[str, Any]:
    manifest = Path(manifest_path)
    if not manifest.is_file():
        raise FileNotFoundError(f"manifest file does not exist: {manifest}")

    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    packs_dir = output / "packs"
    generated_dir = output / "generated"
    packs_dir.mkdir(parents=True, exist_ok=True)
    generated_dir.mkdir(parents=True, exist_ok=True)

    manual_constraints = _load_manual_constraints(manual_constraints_path, manifest.parent)
    rows = _read_manifest(manifest)
    ledger_rows = [
        _run_row(row, index, manifest.parent, output, packs_dir, generated_dir, manual_constraints)
        for index, row in enumerate(rows, start=1)
    ]
    _write_ledger(output / "ledger.csv", ledger_rows)
    summary = _summary(manifest, output, ledger_rows)
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _run_row(
    row: dict[str, str],
    index: int,
    base_dir: Path,
    output: Path,
    packs_dir: Path,
    generated_dir: Path,
    manual_constraints: dict[str, dict[int, dict[str, str]]],
) -> dict[str, str]:
    record_id = (row.get("record_id") or "").strip()
    if not record_id:
        return _failure_row(row, index, "unknown", "manifest_error", "ManifestError", "record_id is required")

    safe_id = _safe_id(record_id)
    pack_path = packs_dir / f"{safe_id}.json"
    try:
        statement_path = _resolve_existing_path(row, "statement", base_dir)
        formulation_value = (row.get("formulation") or "").strip()
        if formulation_value:
            row_type = "materialized_formulation"
            formulation_path = _resolve_existing_path(row, "formulation", base_dir)
            problem_id = _problem_id(row, index)
            problem_path, submission_path = materialize_formulation(
                formulation_path,
                problem_id=problem_id,
                output_dir=generated_dir / safe_id,
                record_id=record_id,
                manual_constraints=manual_constraints.get(record_id, {}),
            )
        else:
            row_type = "existing_or_ci_inputs"
            formulation_path = None
            problem_path = _resolve_existing_path(row, "problem", base_dir)
            submission_path = _resolve_existing_path(row, "submission", base_dir)
            problem_id = ""

        report = verify(problem_path, submission_path)
        pack = build_evidence_pack(statement_path, problem_path, submission_path, report)
        write_evidence_pack(pack, pack_path)
        report_data = report.to_dict()
        if not problem_id:
            problem_id = str(report_data["problem_id"])
        return {
            "record_id": record_id,
            "row_index": str(index),
            "row_type": row_type,
            "row_status": "evidence_pack_written",
            "problem_id": problem_id,
            "verification_status": str(report_data["status"]),
            "classification": str(report_data["classification"]),
            "statement_path": str(statement_path),
            "formulation_path": str(formulation_path) if formulation_path else "",
            "problem_path": str(problem_path),
            "submission_path": str(submission_path),
            "evidence_pack_path": str(pack_path),
            "error_type": "",
            "error_message": "",
        }
    except FormulationAdapterError as exc:
        return _failure_row(row, index, record_id, "formulation_unsupported", type(exc).__name__, str(exc))
    except Exception as exc:
        return _failure_row(row, index, record_id, "row_failed", type(exc).__name__, str(exc))


def _failure_row(
    row: dict[str, str],
    index: int,
    record_id: str,
    status: str,
    error_type: str,
    error_message: str,
) -> dict[str, str]:
    return {
        "record_id": record_id,
        "row_index": str(index),
        "row_type": "materialized_formulation" if (row.get("formulation") or "").strip() else "existing_or_ci_inputs",
        "row_status": status,
        "problem_id": "",
        "verification_status": "",
        "classification": "",
        "statement_path": row.get("statement", ""),
        "formulation_path": row.get("formulation", ""),
        "problem_path": row.get("problem", ""),
        "submission_path": row.get("submission", ""),
        "evidence_pack_path": "",
        "error_type": error_type,
        "error_message": error_message,
    }


def _read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("manifest must have a header row")
        return [{key: value or "" for key, value in row.items()} for row in reader]


def _write_ledger(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _summary(manifest: Path, output: Path, rows: list[dict[str, str]]) -> dict[str, Any]:
    counts = Counter(row["row_status"] for row in rows)
    return {
        "schema_version": SCHEMA_VERSION,
        "manifest_path": str(manifest),
        "output_dir": str(output),
        "row_count": len(rows),
        "succeeded": counts.get("evidence_pack_written", 0),
        "failed": len(rows) - counts.get("evidence_pack_written", 0),
        "counts_by_row_status": dict(sorted(counts.items())),
        "source_fidelity_boundary": {
            "or_ci_pass_means": "configured deterministic verifier checks passed",
            "non_claims": [
                "Batch evidence does not parse source statements into optimization models.",
                "Batch evidence does not call an LLM or external network service.",
                "OR-CI PASS is not proof of source-statement correctness.",
                "Formulation materialization is adapter evidence, not a source-fidelity judgment.",
            ],
        },
    }


def _resolve_existing_path(row: dict[str, str], field: str, base_dir: Path) -> Path:
    value = (row.get(field) or "").strip()
    if not value:
        raise FileNotFoundError(f"{field} path is required")
    path = Path(value)
    if not path.is_absolute():
        path = base_dir / path
    if not path.is_file():
        raise FileNotFoundError(f"{field} file does not exist: {path}")
    return path


def _problem_id(row: dict[str, str], index: int) -> str:
    supplied = (row.get("problem_id") or "").strip()
    if not supplied:
        return f"BWOR-BATCH-{index:03d}"
    if not supplied.startswith("BWOR-"):
        raise FormulationAdapterError("problem_id must start with BWOR-")
    return supplied


def _load_manual_constraints(
    path: str | Path | None,
    base_dir: Path,
) -> dict[str, dict[int, dict[str, str]]]:
    if path is None:
        return {}
    manual_path = Path(path)
    if not manual_path.is_absolute():
        manual_path = base_dir / manual_path
    if not manual_path.is_file():
        raise FileNotFoundError(f"manual constraints file does not exist: {manual_path}")
    result: dict[str, dict[int, dict[str, str]]] = {}
    with manual_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("status") and row.get("status") != "active":
                continue
            record_id = row.get("record_id") or row.get("mutation_id") or ""
            constraint_type = row.get("constraint_type") or ""
            constraint_index = row.get("constraint_index") or ""
            if not record_id or constraint_type != "xy" or not constraint_index.isdigit():
                continue
            result.setdefault(record_id, {})[int(constraint_index)] = {key: value or "" for key, value in row.items()}
    return result


def _safe_id(value: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return safe or "record"
