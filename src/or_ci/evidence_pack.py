from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from or_ci.contracts import ProblemMetadata, VerificationReport
from or_ci.metadata import load_problem_metadata


SCHEMA_VERSION = "or_ci_evidence_pack_v1"


def build_evidence_pack(
    statement_path: str | Path,
    problem_path: str | Path,
    submission_path: str | Path,
    report: VerificationReport,
) -> dict[str, Any]:
    problem = load_problem_metadata(problem_path)
    report_data = report.to_dict()
    return {
        "schema_version": SCHEMA_VERSION,
        "source_statement": _file_identity(statement_path),
        "problem_metadata": _problem_identity(problem_path, problem),
        "submission": _file_identity(submission_path),
        "verification_report": report_data,
        "answer_evidence": _answer_evidence(report_data),
        "source_fidelity_boundary": {
            "statement_used_as_provenance_only": True,
            "or_ci_pass_means": "configured deterministic verifier checks passed",
            "non_claims": [
                "OR-CI does not parse the source statement into a model.",
                "OR-CI does not call an LLM or external network service.",
                "OR-CI PASS is not proof of source-statement correctness.",
                "This pack is evidence for downstream source-fidelity review, not the review itself.",
            ],
        },
    }


def write_evidence_pack(pack: dict[str, Any], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(pack, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _file_identity(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    stat = file_path.stat()
    return {
        "path": str(file_path),
        "resolved_path": str(file_path.resolve()),
        "exists": True,
        "sha256": _sha256(file_path),
        "size_bytes": stat.st_size,
    }


def _problem_identity(path: str | Path, problem: ProblemMetadata) -> dict[str, Any]:
    identity = _file_identity(path)
    identity["problem_id"] = problem.id
    identity["problem_type"] = problem.problem_type
    return identity


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _answer_evidence(report_data: dict[str, Any]) -> dict[str, Any]:
    original_status = report_data.get("solver_status", {}).get("original")
    objective_value = None
    if isinstance(original_status, dict):
        objective_value = original_status.get("objective_value")
    return {
        "verification_status": report_data["status"],
        "classification": report_data["classification"],
        "original_solver_status": original_status,
        "original_objective_value": objective_value,
        "answer_available": objective_value is not None,
        "answer_source": (
            "verification_report.solver_status.original.objective_value"
            if objective_value is not None
            else None
        ),
    }
