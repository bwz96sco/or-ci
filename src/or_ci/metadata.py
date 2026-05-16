from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from or_ci.contracts import (
    ConstraintRelaxationConfig,
    ConstraintRelaxationSpec,
    CostScalingConfig,
    ProblemMetadata,
)


class MetadataError(ValueError):
    """Raised when problem metadata is malformed."""


def load_problem_metadata(path: str | Path) -> ProblemMetadata:
    metadata_path = Path(path)
    with metadata_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    if not isinstance(raw, dict):
        raise MetadataError("problem metadata must be a JSON object")

    _require(raw, "id", str)
    _require(raw, "problem_type", str)
    _require(raw, "instance", dict)
    _require(raw, "metamorphic", dict)

    metamorphic = raw["metamorphic"]
    if not isinstance(metamorphic.get("cost_scaling"), dict):
        raise MetadataError("metamorphic.cost_scaling is required")

    scaling = metamorphic["cost_scaling"]
    coefficient_paths = scaling.get("coefficient_paths")
    factors = scaling.get("factors")
    if not isinstance(coefficient_paths, list) or not coefficient_paths:
        raise MetadataError("cost_scaling.coefficient_paths must be a non-empty list")
    if not all(isinstance(item, str) and item for item in coefficient_paths):
        raise MetadataError("cost_scaling.coefficient_paths entries must be strings")
    if not isinstance(factors, list) or not factors:
        raise MetadataError("cost_scaling.factors must be a non-empty list")
    if not all(_is_positive_number(item) for item in factors):
        raise MetadataError("cost_scaling.factors entries must be positive numbers")

    tolerance_abs = scaling.get("tolerance_abs", 1e-6)
    tolerance_rel = scaling.get("tolerance_rel", 1e-6)
    if not _is_non_negative_number(tolerance_abs):
        raise MetadataError("cost_scaling.tolerance_abs must be a non-negative number")
    if not _is_non_negative_number(tolerance_rel):
        raise MetadataError("cost_scaling.tolerance_rel must be a non-negative number")

    constraint_relaxation = _parse_constraint_relaxation(metamorphic)

    return ProblemMetadata(
        id=raw["id"],
        problem_type=raw["problem_type"],
        instance=raw["instance"],
        cost_scaling=CostScalingConfig(
            coefficient_paths=coefficient_paths,
            factors=[float(item) for item in factors],
            tolerance_abs=float(tolerance_abs),
            tolerance_rel=float(tolerance_rel),
        ),
        constraint_relaxation=constraint_relaxation,
        evaluation_only=_parse_evaluation_only(raw),
    )


def _parse_constraint_relaxation(metamorphic: dict[str, Any]) -> ConstraintRelaxationConfig | None:
    raw = metamorphic.get("constraint_relaxation")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise MetadataError("metamorphic.constraint_relaxation must be an object when present")

    tolerance_abs = raw.get("tolerance_abs", 1e-6)
    tolerance_rel = raw.get("tolerance_rel", 1e-6)
    if not _is_non_negative_number(tolerance_abs):
        raise MetadataError("constraint_relaxation.tolerance_abs must be a non-negative number")
    if not _is_non_negative_number(tolerance_rel):
        raise MetadataError("constraint_relaxation.tolerance_rel must be a non-negative number")

    relaxations = raw.get("relaxations")
    if not isinstance(relaxations, list) or not relaxations:
        raise MetadataError("constraint_relaxation.relaxations must be a non-empty list")

    parsed = []
    allowed_relations = {"non_decrease", "increase", "non_increase", "decrease"}
    for index, relaxation in enumerate(relaxations):
        if not isinstance(relaxation, dict):
            raise MetadataError("constraint_relaxation.relaxations entries must be objects")
        name = relaxation.get("name", f"relaxation_{index}")
        paths = relaxation.get("paths")
        factor = relaxation.get("factor")
        relation = relaxation.get("objective_relation")
        if not isinstance(name, str) or not name:
            raise MetadataError("constraint_relaxation relaxation name must be a non-empty string")
        if not isinstance(paths, list) or not paths:
            raise MetadataError(f"constraint_relaxation.{name}.paths must be a non-empty list")
        if not all(isinstance(path, str) and path for path in paths):
            raise MetadataError(f"constraint_relaxation.{name}.paths entries must be strings")
        if not _is_positive_number(factor):
            raise MetadataError(f"constraint_relaxation.{name}.factor must be a positive number")
        if relation not in allowed_relations:
            raise MetadataError(
                f"constraint_relaxation.{name}.objective_relation must be one of {sorted(allowed_relations)}"
            )
        parsed.append(
            ConstraintRelaxationSpec(
                name=name,
                paths=paths,
                factor=float(factor),
                objective_relation=relation,
            )
        )

    return ConstraintRelaxationConfig(
        relaxations=parsed,
        tolerance_abs=float(tolerance_abs),
        tolerance_rel=float(tolerance_rel),
    )


def _parse_evaluation_only(raw: dict[str, Any]) -> dict[str, Any]:
    evaluation_only = raw.get("evaluation_only", {})
    if evaluation_only is not None and not isinstance(evaluation_only, dict):
        raise MetadataError("evaluation_only must be an object when present")
    return evaluation_only or {}


def _require(raw: dict[str, Any], key: str, expected_type: type) -> None:
    if key not in raw:
        raise MetadataError(f"{key} is required")
    if not isinstance(raw[key], expected_type):
        raise MetadataError(f"{key} must be {expected_type.__name__}")


def _is_positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _is_non_negative_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0
