from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from or_ci.contracts import (
    ConstraintRelaxationConfig,
    ConstraintRelaxationSpec,
    CostScalingConfig,
    GoalProgrammingConfig,
    GoalSpec,
    LinearExpressionConfig,
    ObjectiveCheckConfig,
    ProblemMetadata,
    ScenarioMetadata,
)


class MetadataError(ValueError):
    """Raised when problem metadata is malformed."""


_PROBLEM_TYPES = {"LP", "MILP", "QP", "MIQP", "MULTI_SCENARIO"}
_SCENARIO_SOLVER_STATUSES = {
    "OPTIMAL",
    "INFEASIBLE",
    "INF_OR_UNBD",
    "UNBOUNDED",
    "TIME_LIMIT",
    "NUMERIC",
    "SUBOPTIMAL",
}


def load_problem_metadata(path: str | Path) -> ProblemMetadata:
    metadata_path = Path(path)
    with metadata_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    if not isinstance(raw, dict):
        raise MetadataError("problem metadata must be a JSON object")

    _require(raw, "id", str)
    _require(raw, "problem_type", str)
    if raw["problem_type"] not in _PROBLEM_TYPES:
        raise MetadataError(f"problem_type must be one of {sorted(_PROBLEM_TYPES)}")

    scenarios = _parse_scenarios(raw)
    if scenarios:
        if raw["problem_type"] != "MULTI_SCENARIO":
            raise MetadataError("problem_type must be MULTI_SCENARIO when scenarios are present")
        return ProblemMetadata(
            id=raw["id"],
            problem_type=raw["problem_type"],
            instance=_optional_object(raw, "instance"),
            scenarios=scenarios,
            evaluation_only=_parse_evaluation_only(raw),
        )

    if raw["problem_type"] == "MULTI_SCENARIO":
        raise MetadataError("scenarios must be a non-empty list for MULTI_SCENARIO problems")

    _require(raw, "instance", dict)
    _require(raw, "metamorphic", dict)
    metamorphic = raw["metamorphic"]
    cost_scaling = _parse_cost_scaling(metamorphic, required=True)
    constraint_relaxation = _parse_constraint_relaxation(metamorphic)
    goal_programming = _parse_goal_programming(metamorphic)

    return ProblemMetadata(
        id=raw["id"],
        problem_type=raw["problem_type"],
        instance=raw["instance"],
        cost_scaling=cost_scaling,
        constraint_relaxation=constraint_relaxation,
        goal_programming=goal_programming,
        evaluation_only=_parse_evaluation_only(raw),
    )


def _parse_cost_scaling(metamorphic: dict[str, Any], *, required: bool) -> CostScalingConfig | None:
    raw = metamorphic.get("cost_scaling")
    if raw is None:
        if required:
            raise MetadataError("metamorphic.cost_scaling is required")
        return None
    if not isinstance(raw, dict):
        raise MetadataError("metamorphic.cost_scaling must be an object")

    coefficient_paths = raw.get("coefficient_paths")
    factors = raw.get("factors")
    if not isinstance(coefficient_paths, list) or not coefficient_paths:
        raise MetadataError("cost_scaling.coefficient_paths must be a non-empty list")
    if not all(isinstance(item, str) and item for item in coefficient_paths):
        raise MetadataError("cost_scaling.coefficient_paths entries must be strings")
    if not isinstance(factors, list) or not factors:
        raise MetadataError("cost_scaling.factors must be a non-empty list")
    if not all(_is_positive_number(item) for item in factors):
        raise MetadataError("cost_scaling.factors entries must be positive numbers")

    tolerance_abs = raw.get("tolerance_abs", 1e-6)
    tolerance_rel = raw.get("tolerance_rel", 1e-6)
    if not _is_non_negative_number(tolerance_abs):
        raise MetadataError("cost_scaling.tolerance_abs must be a non-negative number")
    if not _is_non_negative_number(tolerance_rel):
        raise MetadataError("cost_scaling.tolerance_rel must be a non-negative number")

    return CostScalingConfig(
        coefficient_paths=coefficient_paths,
        factors=[float(item) for item in factors],
        tolerance_abs=float(tolerance_abs),
        tolerance_rel=float(tolerance_rel),
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


def _parse_goal_programming(metamorphic: dict[str, Any]) -> GoalProgrammingConfig | None:
    raw = metamorphic.get("goal_programming")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise MetadataError("metamorphic.goal_programming must be an object when present")

    mode = raw.get("mode")
    if mode not in {"weighted", "lexicographic"}:
        raise MetadataError("goal_programming.mode must be one of ['lexicographic', 'weighted']")
    objective_sense = raw.get("objective_sense")
    if objective_sense not in {"min", "max"}:
        raise MetadataError("goal_programming.objective_sense must be one of ['max', 'min']")

    tolerance_abs = raw.get("tolerance_abs", 1e-6)
    tolerance_rel = raw.get("tolerance_rel", 1e-6)
    if not _is_non_negative_number(tolerance_abs):
        raise MetadataError("goal_programming.tolerance_abs must be a non-negative number")
    if not _is_non_negative_number(tolerance_rel):
        raise MetadataError("goal_programming.tolerance_rel must be a non-negative number")

    raw_goals = raw.get("goals")
    if not isinstance(raw_goals, list) or not raw_goals:
        raise MetadataError("goal_programming.goals must be a non-empty list")

    goals = []
    seen_names: set[str] = set()
    seen_priorities: set[int] = set()
    for goal in raw_goals:
        if not isinstance(goal, dict):
            raise MetadataError("goal_programming.goals entries must be objects")
        name = goal.get("name")
        if not isinstance(name, str) or not name:
            raise MetadataError("goal_programming goal name must be a non-empty string")
        if name in seen_names:
            raise MetadataError(f"goal_programming goal name is duplicated: {name}")
        seen_names.add(name)
        expression = _parse_linear_expression(goal.get("expression"), f"goal_programming.{name}.expression")

        weight = goal.get("weight")
        priority = goal.get("priority")
        priority_weight = goal.get("priority_weight")
        if mode == "weighted":
            if not _is_positive_number(weight):
                raise MetadataError(f"goal_programming.{name}.weight must be a positive number")
            goals.append(GoalSpec(name=name, expression=expression, weight=float(weight)))
        else:
            if not isinstance(priority, int) or isinstance(priority, bool) or priority <= 0:
                raise MetadataError(f"goal_programming.{name}.priority must be a positive integer")
            if priority in seen_priorities:
                raise MetadataError(f"goal_programming priority is duplicated: {priority}")
            seen_priorities.add(priority)
            if not _is_positive_number(priority_weight):
                raise MetadataError(f"goal_programming.{name}.priority_weight must be a positive number")
            goals.append(
                GoalSpec(
                    name=name,
                    expression=expression,
                    priority=priority,
                    priority_weight=float(priority_weight),
                )
            )

    if mode == "lexicographic":
        sorted_goals = sorted(goals, key=lambda item: item.priority or 0)
        weights = [goal.priority_weight or 0.0 for goal in sorted_goals]
        if any(left <= right for left, right in zip(weights, weights[1:])):
            raise MetadataError("goal_programming priority_weight values must strictly decrease by priority")

    return GoalProgrammingConfig(
        mode=mode,
        objective_sense=objective_sense,
        goals=goals,
        tolerance_abs=float(tolerance_abs),
        tolerance_rel=float(tolerance_rel),
    )


def _parse_linear_expression(raw: Any, field: str) -> LinearExpressionConfig:
    if not isinstance(raw, dict):
        raise MetadataError(f"{field} must be an object")
    variables = raw.get("variables")
    if not isinstance(variables, dict) or not variables:
        raise MetadataError(f"{field}.variables must be a non-empty object")
    parsed_variables: dict[str, float] = {}
    for name, coefficient in variables.items():
        if not isinstance(name, str) or not name:
            raise MetadataError(f"{field}.variables keys must be non-empty strings")
        if not _is_number(coefficient):
            raise MetadataError(f"{field}.variables.{name} must be a number")
        parsed_variables[name] = float(coefficient)
    constant = raw.get("constant", 0.0)
    if not _is_number(constant):
        raise MetadataError(f"{field}.constant must be a number")
    return LinearExpressionConfig(variables=parsed_variables, constant=float(constant))


def _parse_scenarios(raw: dict[str, Any]) -> list[ScenarioMetadata]:
    scenarios = raw.get("scenarios")
    if scenarios is None:
        return []
    if not isinstance(scenarios, list) or not scenarios:
        raise MetadataError("scenarios must be a non-empty list when present")

    parsed = []
    seen_names: set[str] = set()
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise MetadataError("scenarios entries must be objects")
        name = scenario.get("name")
        if not isinstance(name, str) or not name:
            raise MetadataError("scenario name must be a non-empty string")
        if name in seen_names:
            raise MetadataError(f"scenario name is duplicated: {name}")
        seen_names.add(name)
        instance = scenario.get("instance")
        if not isinstance(instance, dict):
            raise MetadataError(f"scenario.{name}.instance must be an object")
        problem_type = scenario.get("problem_type", "LP")
        scenario_problem_types = _PROBLEM_TYPES - {"MULTI_SCENARIO"}
        if problem_type not in scenario_problem_types:
            raise MetadataError(
                f"scenario.{name}.problem_type must be one of {sorted(scenario_problem_types)}"
            )
        expected = scenario.get("expected_solver_status")
        if expected not in _SCENARIO_SOLVER_STATUSES:
            raise MetadataError(
                f"scenario.{name}.expected_solver_status must be one of {sorted(_SCENARIO_SOLVER_STATUSES)}"
            )
        required = scenario.get("required", True)
        if not isinstance(required, bool):
            raise MetadataError(f"scenario.{name}.required must be a boolean")
        metamorphic = scenario.get("metamorphic", {})
        if not isinstance(metamorphic, dict):
            raise MetadataError(f"scenario.{name}.metamorphic must be an object when present")
        parsed.append(
            ScenarioMetadata(
                name=name,
                instance=instance,
                expected_solver_status=expected,
                problem_type=problem_type,
                cost_scaling=_parse_cost_scaling(metamorphic, required=False),
                constraint_relaxation=_parse_constraint_relaxation(metamorphic),
                goal_programming=_parse_goal_programming(metamorphic),
                objective_check=_parse_objective_check(scenario.get("objective"), name),
                required=required,
            )
        )
    return parsed


def _parse_objective_check(raw: Any, scenario_name: str) -> ObjectiveCheckConfig | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise MetadataError(f"scenario.{scenario_name}.objective must be an object when present")
    value = raw.get("value")
    if not _is_number(value):
        raise MetadataError(f"scenario.{scenario_name}.objective.value must be a number")
    relation = raw.get("relation", "equal")
    allowed = {"equal", "non_decrease", "increase", "non_increase", "decrease"}
    if relation not in allowed:
        raise MetadataError(f"scenario.{scenario_name}.objective.relation must be one of {sorted(allowed)}")
    tolerance_abs = raw.get("tolerance_abs", 1e-6)
    tolerance_rel = raw.get("tolerance_rel", 1e-6)
    if not _is_non_negative_number(tolerance_abs):
        raise MetadataError(f"scenario.{scenario_name}.objective.tolerance_abs must be a non-negative number")
    if not _is_non_negative_number(tolerance_rel):
        raise MetadataError(f"scenario.{scenario_name}.objective.tolerance_rel must be a non-negative number")
    return ObjectiveCheckConfig(
        value=float(value),
        relation=relation,
        tolerance_abs=float(tolerance_abs),
        tolerance_rel=float(tolerance_rel),
    )


def _parse_evaluation_only(raw: dict[str, Any]) -> dict[str, Any]:
    evaluation_only = raw.get("evaluation_only", {})
    if evaluation_only is not None and not isinstance(evaluation_only, dict):
        raise MetadataError("evaluation_only must be an object when present")
    return evaluation_only or {}


def _optional_object(raw: dict[str, Any], key: str) -> dict[str, Any]:
    value = raw.get(key, {})
    if value is not None and not isinstance(value, dict):
        raise MetadataError(f"{key} must be an object when present")
    return value or {}


def _require(raw: dict[str, Any], key: str, expected_type: type) -> None:
    if key not in raw:
        raise MetadataError(f"{key} is required")
    if not isinstance(raw[key], expected_type):
        raise MetadataError(f"{key} must be {expected_type.__name__}")


def _is_positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _is_non_negative_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
