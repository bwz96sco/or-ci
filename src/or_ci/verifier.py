from __future__ import annotations

import copy
import math
from pathlib import Path
from typing import Any

from gurobipy import GRB

from or_ci.contracts import (
    CheckResult,
    Classification,
    CostScalingConfig,
    GoalProgrammingConfig,
    LinearExpressionConfig,
    ObjectiveCheckConfig,
    ProblemMetadata,
    ScenarioMetadata,
    VerificationReport,
    VerificationStatus,
)
from or_ci.metadata import load_problem_metadata
from or_ci.model_ir import UnsupportedModelFeature, extract_model_ir
from or_ci.scaling import scale_numeric_paths, scaled_instance
from or_ci.submission import load_build_model


def verify(problem_path: str | Path, submission_path: str | Path) -> VerificationReport:
    problem = load_problem_metadata(problem_path)
    return verify_problem(problem, submission_path)


def verify_problem(problem: ProblemMetadata, submission_path: str | Path) -> VerificationReport:
    submission = str(Path(submission_path))
    solver_status: dict[str, Any] = {}
    checks: list[CheckResult] = []
    failures: list[dict[str, Any]] = []
    model_ir_summary: dict[str, int] = {}

    try:
        build_model = load_build_model(submission_path)
        if problem.scenarios:
            return _verify_scenarios(problem, submission, build_model)

        original_model = build_model(copy.deepcopy(problem.instance))
        model_ir = extract_model_ir(original_model)
        _validate_model_type_support(problem.problem_type, model_ir)
        model_ir_summary = model_ir.summary

        original_result = _optimize(original_model)
        solver_status["original"] = original_result
        checks.append(
            CheckResult(
                name="original_solver_status",
                status="PASS" if original_result["is_optimal"] else "FAIL",
                details=original_result,
            )
        )
        if not original_result["is_optimal"]:
            failures.append(
                {
                    "check": "original_solver_status",
                    "message": "original model did not solve to optimality",
                    "observed_status": original_result,
                }
            )
            return _report(
                problem,
                submission,
                Classification.SOLVER_STATUS_ERROR,
                solver_status,
                model_ir_summary,
                checks,
                failures,
            )

        original_obj = float(original_result["objective_value"])
        classification = _run_goal_programming_check(
            problem.goal_programming,
            model_ir,
            original_model,
            original_obj,
            checks,
            failures,
        )
        if classification is not None:
            return _report(
                problem,
                submission,
                classification,
                solver_status,
                model_ir_summary,
                checks,
                failures,
            )

        classification = _run_cost_scaling_checks(
            problem.instance,
            problem.cost_scaling,
            build_model,
            original_obj,
            solver_status,
            checks,
            failures,
        )
        if classification is not None:
            return _report(
                problem,
                submission,
                classification,
                solver_status,
                model_ir_summary,
                checks,
                failures,
            )

        classification = _run_constraint_relaxation_checks(
            problem.instance,
            problem.constraint_relaxation,
            build_model,
            original_obj,
            solver_status,
            checks,
            failures,
        )
        if classification is not None:
            return _report(
                problem,
                submission,
                classification,
                solver_status,
                model_ir_summary,
                checks,
                failures,
            )

        return _report(
            problem,
            submission,
            Classification.SUCCESS,
            solver_status,
            model_ir_summary,
            checks,
            failures,
        )
    except UnsupportedModelFeature as exc:
        failures.append({"check": "model_ir", "message": str(exc)})
        return _report(
            problem,
            submission,
            Classification.UNSUPPORTED_MODEL_FEATURE,
            solver_status,
            model_ir_summary,
            checks,
            failures,
        )
    except Exception as exc:
        failures.append({"check": "submission", "message": str(exc), "error_type": type(exc).__name__})
        return _report(
            problem,
            submission,
            Classification.SYNTAX_OR_RUNTIME_ERROR,
            solver_status,
            model_ir_summary,
            checks,
            failures,
        )


def _optimize(model: Any) -> dict[str, Any]:
    set_param = getattr(model, "setParam", None)
    if callable(set_param):
        set_param("OutputFlag", 0)
    model.optimize()
    status_code = int(getattr(model, "Status"))
    result: dict[str, Any] = {
        "code": status_code,
        "name": _solver_status_name(status_code),
        "is_optimal": status_code == GRB.OPTIMAL,
    }
    if result["is_optimal"]:
        result["objective_value"] = float(getattr(model, "ObjVal"))
    return result


def _validate_model_type_support(problem_type: str, model_ir: Any) -> None:
    if model_ir.objective.quadratic_terms and problem_type not in {"QP", "MIQP"}:
        raise UnsupportedModelFeature("quadratic objective terms require problem_type QP or MIQP")


def _run_cost_scaling_checks(
    instance: dict[str, Any],
    config: CostScalingConfig | None,
    build_model: Any,
    original_obj: float,
    solver_status: dict[str, Any],
    checks: list[CheckResult],
    failures: list[dict[str, Any]],
    *,
    check_name: str = "cost_scaling",
    status_key_prefix: str = "scaled",
    detail_extra: dict[str, Any] | None = None,
) -> Classification | None:
    if config is None:
        return None

    detail_extra = detail_extra or {}
    for factor in config.factors:
        scaled_data = scaled_instance(instance, config, factor)
        scaled_model = build_model(scaled_data)
        scaled_result = _optimize(scaled_model)
        solver_status[f"{status_key_prefix}_{factor:g}"] = scaled_result
        if not scaled_result["is_optimal"]:
            checks.append(
                CheckResult(
                    name=check_name,
                    status="FAIL",
                    details={"factor": factor, "scaled_solver_status": scaled_result, **detail_extra},
                )
            )
            failures.append(
                {
                    "check": check_name,
                    "message": "scaled model did not solve to optimality",
                    "factor": factor,
                    "observed_status": scaled_result,
                    **detail_extra,
                }
            )
            return Classification.SOLVER_STATUS_ERROR

        scaled_obj = float(scaled_result["objective_value"])
        expected_obj = factor * original_obj
        passed = math.isclose(
            scaled_obj,
            expected_obj,
            rel_tol=config.tolerance_rel,
            abs_tol=config.tolerance_abs,
        )
        details = {
            "factor": factor,
            "original_objective": original_obj,
            "scaled_objective": scaled_obj,
            "expected_scaled_objective": expected_obj,
            "tolerance_abs": config.tolerance_abs,
            "tolerance_rel": config.tolerance_rel,
            "expected_relation": "scaled_obj ~= factor * original_obj",
            **detail_extra,
        }
        checks.append(CheckResult(name=check_name, status="PASS" if passed else "FAIL", details=details))
        if not passed:
            failures.append(
                {
                    "check": check_name,
                    "message": "scaled objective did not match the cost-scaling invariant",
                    **details,
                }
            )
            return Classification.RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL
    return None


def _run_constraint_relaxation_checks(
    instance: dict[str, Any],
    config: Any,
    build_model: Any,
    original_obj: float,
    solver_status: dict[str, Any],
    checks: list[CheckResult],
    failures: list[dict[str, Any]],
    *,
    check_name: str = "constraint_relaxation",
    status_key_prefix: str = "relaxed",
    detail_extra: dict[str, Any] | None = None,
) -> Classification | None:
    if config is None:
        return None

    detail_extra = detail_extra or {}
    for relaxation in config.relaxations:
        relaxed_data = scale_numeric_paths(
            instance,
            relaxation.paths,
            relaxation.factor,
            context="constraint-relaxation",
        )
        relaxed_model = build_model(relaxed_data)
        relaxed_result = _optimize(relaxed_model)
        status_key = f"{status_key_prefix}_{relaxation.name}"
        solver_status[status_key] = relaxed_result
        if not relaxed_result["is_optimal"]:
            checks.append(
                CheckResult(
                    name=check_name,
                    status="FAIL",
                    details={
                        "relaxation": relaxation.name,
                        "relaxed_solver_status": relaxed_result,
                        **detail_extra,
                    },
                )
            )
            failures.append(
                {
                    "check": check_name,
                    "message": "relaxed model did not solve to optimality",
                    "relaxation": relaxation.name,
                    "observed_status": relaxed_result,
                    **detail_extra,
                }
            )
            return Classification.SOLVER_STATUS_ERROR

        relaxed_obj = float(relaxed_result["objective_value"])
        passed = _objective_relation_holds(
            original_obj,
            relaxed_obj,
            relaxation.objective_relation,
            config.tolerance_abs,
            config.tolerance_rel,
        )
        details = {
            "relaxation": relaxation.name,
            "paths": relaxation.paths,
            "factor": relaxation.factor,
            "original_objective": original_obj,
            "relaxed_objective": relaxed_obj,
            "objective_relation": relaxation.objective_relation,
            "tolerance_abs": config.tolerance_abs,
            "tolerance_rel": config.tolerance_rel,
            **detail_extra,
        }
        checks.append(
            CheckResult(name=check_name, status="PASS" if passed else "FAIL", details=details)
        )
        if not passed:
            failures.append(
                {
                    "check": check_name,
                    "message": "relaxed objective did not satisfy the configured relation",
                    **details,
                }
            )
            return Classification.RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL
    return None


def _run_goal_programming_check(
    config: GoalProgrammingConfig | None,
    model_ir: Any,
    model: Any,
    observed_objective: float,
    checks: list[CheckResult],
    failures: list[dict[str, Any]],
    *,
    check_name: str = "goal_programming",
    detail_extra: dict[str, Any] | None = None,
) -> Classification | None:
    if config is None:
        return None

    detail_extra = detail_extra or {}
    solution_values = _solution_values(model)
    try:
        expected_coefficients, expected_constant, goal_values = _goal_scalarization(config, solution_values)
    except ValueError as exc:
        details = {"message": str(exc), **detail_extra}
        checks.append(CheckResult(name=check_name, status="FAIL", details=details))
        failures.append({"check": check_name, **details})
        return Classification.RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL

    coefficient_diffs = _objective_coefficient_differences(
        model_ir.objective.coefficients,
        expected_coefficients,
        tolerance_abs=config.tolerance_abs,
        tolerance_rel=config.tolerance_rel,
    )
    constant_matches = math.isclose(
        model_ir.objective.constant,
        expected_constant,
        rel_tol=config.tolerance_rel,
        abs_tol=config.tolerance_abs,
    )
    expected_objective = sum(item["weighted_value"] for item in goal_values)
    objective_matches = math.isclose(
        observed_objective,
        expected_objective,
        rel_tol=config.tolerance_rel,
        abs_tol=config.tolerance_abs,
    )
    passed = (
        model_ir.objective.sense == config.objective_sense
        and not model_ir.objective.quadratic_terms
        and not coefficient_diffs
        and constant_matches
        and objective_matches
    )
    details = {
        "mode": config.mode,
        "objective_sense": config.objective_sense,
        "observed_model_sense": model_ir.objective.sense,
        "goal_values": goal_values,
        "observed_objective": observed_objective,
        "expected_objective": expected_objective,
        "expected_coefficients": expected_coefficients,
        "observed_coefficients": model_ir.objective.coefficients,
        "coefficient_differences": coefficient_diffs,
        "expected_constant": expected_constant,
        "observed_constant": model_ir.objective.constant,
        "quadratic_terms": [term.__dict__ for term in model_ir.objective.quadratic_terms],
        "tolerance_abs": config.tolerance_abs,
        "tolerance_rel": config.tolerance_rel,
        **detail_extra,
    }
    checks.append(CheckResult(name=check_name, status="PASS" if passed else "FAIL", details=details))
    if not passed:
        failures.append(
            {
                "check": check_name,
                "message": "goal-programming objective did not match the configured scalarization",
                **details,
            }
        )
        return Classification.RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL
    return None


def _goal_scalarization(
    config: GoalProgrammingConfig,
    solution_values: dict[str, float],
) -> tuple[dict[str, float], float, list[dict[str, Any]]]:
    coefficients: dict[str, float] = {}
    constant = 0.0
    goal_values = []
    for goal in config.goals:
        factor = goal.weight if config.mode == "weighted" else goal.priority_weight
        if factor is None:
            raise ValueError(f"goal {goal.name} is missing scalarization weight")
        value = _linear_expression_value(goal.expression, solution_values)
        weighted_value = factor * value
        constant += factor * goal.expression.constant
        for variable, coefficient in goal.expression.variables.items():
            coefficients[variable] = coefficients.get(variable, 0.0) + factor * coefficient
        goal_values.append(
            {
                "name": goal.name,
                "value": value,
                "weight": factor,
                "weighted_value": weighted_value,
                "priority": goal.priority,
            }
        )
    return ({name: coeff for name, coeff in coefficients.items() if coeff != 0.0}, constant, goal_values)


def _linear_expression_value(expression: LinearExpressionConfig, solution_values: dict[str, float]) -> float:
    value = expression.constant
    for variable, coefficient in expression.variables.items():
        if variable not in solution_values:
            raise ValueError(f"goal expression references unknown solution variable: {variable}")
        value += coefficient * solution_values[variable]
    return value


def _solution_values(model: Any) -> dict[str, float]:
    values = {}
    for var in model.getVars():
        name = str(_get_attr(var, "VarName"))
        values[name] = float(_get_attr(var, "X"))
    return values


def _objective_coefficient_differences(
    observed: dict[str, float],
    expected: dict[str, float],
    *,
    tolerance_abs: float,
    tolerance_rel: float,
) -> dict[str, dict[str, float]]:
    differences = {}
    for variable in sorted(set(observed) | set(expected)):
        observed_value = observed.get(variable, 0.0)
        expected_value = expected.get(variable, 0.0)
        if not math.isclose(observed_value, expected_value, rel_tol=tolerance_rel, abs_tol=tolerance_abs):
            differences[variable] = {"observed": observed_value, "expected": expected_value}
    return differences


def _run_objective_check(
    config: ObjectiveCheckConfig | None,
    observed_objective: float,
    checks: list[CheckResult],
    failures: list[dict[str, Any]],
    *,
    detail_extra: dict[str, Any],
) -> Classification | None:
    if config is None:
        return None
    if config.relation == "equal":
        passed = math.isclose(
            observed_objective,
            config.value,
            rel_tol=config.tolerance_rel,
            abs_tol=config.tolerance_abs,
        )
    else:
        passed = _objective_relation_holds(
            config.value,
            observed_objective,
            config.relation,
            config.tolerance_abs,
            config.tolerance_rel,
        )
    details = {
        "expected_value": config.value,
        "observed_objective": observed_objective,
        "relation": config.relation,
        "tolerance_abs": config.tolerance_abs,
        "tolerance_rel": config.tolerance_rel,
        **detail_extra,
    }
    checks.append(CheckResult(name="scenario_objective", status="PASS" if passed else "FAIL", details=details))
    if not passed:
        failures.append(
            {
                "check": "scenario_objective",
                "message": "scenario objective did not satisfy the configured check",
                **details,
            }
        )
        return Classification.RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL
    return None


def _verify_scenarios(problem: ProblemMetadata, submission: str, build_model: Any) -> VerificationReport:
    solver_status: dict[str, Any] = {}
    checks: list[CheckResult] = []
    failures: list[dict[str, Any]] = []
    model_ir_summary: dict[str, int] = {
        "scenarios": len(problem.scenarios),
        "required_scenarios": sum(1 for scenario in problem.scenarios if scenario.required),
    }
    classification = Classification.SUCCESS

    for scenario in problem.scenarios:
        detail_extra = {"scenario": scenario.name, "required": scenario.required}
        try:
            scenario_classification = _verify_scenario(
                scenario,
                build_model,
                solver_status,
                checks,
                failures,
                model_ir_summary,
                detail_extra,
            )
        except UnsupportedModelFeature as exc:
            failures.append({"check": "scenario_model_ir", "message": str(exc), **detail_extra})
            scenario_classification = Classification.UNSUPPORTED_MODEL_FEATURE
        except Exception as exc:
            failures.append(
                {
                    "check": "scenario_submission",
                    "message": str(exc),
                    "error_type": type(exc).__name__,
                    **detail_extra,
                }
            )
            scenario_classification = Classification.SYNTAX_OR_RUNTIME_ERROR
        if scenario_classification is not None and classification == Classification.SUCCESS:
            classification = scenario_classification

    return _report(problem, submission, classification, solver_status, model_ir_summary, checks, failures)


def _verify_scenario(
    scenario: ScenarioMetadata,
    build_model: Any,
    solver_status: dict[str, Any],
    checks: list[CheckResult],
    failures: list[dict[str, Any]],
    model_ir_summary: dict[str, int],
    detail_extra: dict[str, Any],
) -> Classification | None:
    model = build_model(copy.deepcopy(scenario.instance))
    model_ir = extract_model_ir(model)
    _validate_model_type_support(scenario.problem_type, model_ir)
    model_ir_summary[f"scenario_{scenario.name}_variables"] = model_ir.summary["variables"]
    model_ir_summary[f"scenario_{scenario.name}_constraints"] = model_ir.summary["constraints"]
    model_ir_summary[f"scenario_{scenario.name}_quadratic_objective_terms"] = model_ir.summary[
        "quadratic_objective_terms"
    ]

    result = _optimize(model)
    solver_status[f"scenario_{scenario.name}"] = result
    status_matches = result["name"] == scenario.expected_solver_status
    checks.append(
        CheckResult(
            name="scenario_solver_status",
            status="PASS" if status_matches else "FAIL",
            details={
                "expected_solver_status": scenario.expected_solver_status,
                "observed_solver_status": result,
                **detail_extra,
            },
        )
    )
    if not status_matches:
        failures.append(
            {
                "check": "scenario_solver_status",
                "message": "scenario solver status did not match the expected status",
                "expected_solver_status": scenario.expected_solver_status,
                "observed_solver_status": result,
                **detail_extra,
            }
        )
        return Classification.SOLVER_STATUS_ERROR

    if scenario.expected_solver_status != "OPTIMAL":
        return None

    observed_objective = float(result["objective_value"])
    classification = _run_objective_check(
        scenario.objective_check,
        observed_objective,
        checks,
        failures,
        detail_extra=detail_extra,
    )
    if classification is not None:
        return classification

    classification = _run_goal_programming_check(
        scenario.goal_programming,
        model_ir,
        model,
        observed_objective,
        checks,
        failures,
        check_name="scenario_goal_programming",
        detail_extra=detail_extra,
    )
    if classification is not None:
        return classification

    classification = _run_cost_scaling_checks(
        scenario.instance,
        scenario.cost_scaling,
        build_model,
        observed_objective,
        solver_status,
        checks,
        failures,
        check_name="scenario_cost_scaling",
        status_key_prefix=f"scenario_{scenario.name}_scaled",
        detail_extra=detail_extra,
    )
    if classification is not None:
        return classification

    return _run_constraint_relaxation_checks(
        scenario.instance,
        scenario.constraint_relaxation,
        build_model,
        observed_objective,
        solver_status,
        checks,
        failures,
        check_name="scenario_constraint_relaxation",
        status_key_prefix=f"scenario_{scenario.name}_relaxed",
        detail_extra=detail_extra,
    )


def _objective_relation_holds(
    original_obj: float,
    transformed_obj: float,
    relation: str,
    tolerance_abs: float,
    tolerance_rel: float,
) -> bool:
    tolerance = max(tolerance_abs, tolerance_rel * max(abs(original_obj), abs(transformed_obj)))
    if relation == "non_decrease":
        return transformed_obj + tolerance >= original_obj
    if relation == "increase":
        return transformed_obj > original_obj + tolerance
    if relation == "non_increase":
        return transformed_obj <= original_obj + tolerance
    if relation == "decrease":
        return transformed_obj < original_obj - tolerance
    raise ValueError(f"unsupported objective relation: {relation}")


def _solver_status_name(status_code: int) -> str:
    names = {
        GRB.LOADED: "LOADED",
        GRB.OPTIMAL: "OPTIMAL",
        GRB.INFEASIBLE: "INFEASIBLE",
        GRB.INF_OR_UNBD: "INF_OR_UNBD",
        GRB.UNBOUNDED: "UNBOUNDED",
        GRB.CUTOFF: "CUTOFF",
        GRB.ITERATION_LIMIT: "ITERATION_LIMIT",
        GRB.NODE_LIMIT: "NODE_LIMIT",
        GRB.TIME_LIMIT: "TIME_LIMIT",
        GRB.SOLUTION_LIMIT: "SOLUTION_LIMIT",
        GRB.INTERRUPTED: "INTERRUPTED",
        GRB.NUMERIC: "NUMERIC",
        GRB.SUBOPTIMAL: "SUBOPTIMAL",
        GRB.INPROGRESS: "INPROGRESS",
        GRB.USER_OBJ_LIMIT: "USER_OBJ_LIMIT",
        GRB.WORK_LIMIT: "WORK_LIMIT",
        GRB.MEM_LIMIT: "MEM_LIMIT",
    }
    return names.get(status_code, f"UNKNOWN_{status_code}")


def _get_attr(obj: Any, attr_name: str) -> Any:
    if hasattr(obj, attr_name):
        return getattr(obj, attr_name)
    lower_name = attr_name[0].lower() + attr_name[1:]
    if hasattr(obj, lower_name):
        return getattr(obj, lower_name)
    get_attr = getattr(obj, "getAttr", None)
    if callable(get_attr):
        return get_attr(attr_name)
    raise AttributeError(f"{type(obj).__name__} has no attribute {attr_name}")


def _report(
    problem: ProblemMetadata,
    submission: str,
    classification: Classification,
    solver_status: dict[str, Any],
    model_ir_summary: dict[str, int],
    checks: list[CheckResult],
    failures: list[dict[str, Any]],
) -> VerificationReport:
    return VerificationReport(
        problem_id=problem.id,
        submission=submission,
        status=VerificationStatus.PASS if classification == Classification.SUCCESS else VerificationStatus.FAIL,
        classification=classification,
        solver_status=solver_status,
        model_ir_summary=model_ir_summary,
        checks=checks,
        failures=failures,
        possible_causes=_possible_causes(classification),
    )


def _possible_causes(classification: Classification) -> list[str]:
    if classification == Classification.SUCCESS:
        return []
    if classification == Classification.SYNTAX_OR_RUNTIME_ERROR:
        return [
            "submission import failed",
            "build_model raised an exception",
            "model optimization raised before solver status was available",
        ]
    if classification == Classification.SOLVER_STATUS_ERROR:
        return ["a model solve reached a different status from the configured requirement"]
    if classification == Classification.RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL:
        return [
            "objective coefficients may not use the configured coefficient paths",
            "constraints may not use the configured relaxation paths",
            "goal-programming scalarization may not match the metadata",
            "scenario objective checks may not match the submitted model",
            "objective sign or constant terms may be wrong",
            "the model may be optimizing a different objective from the metadata",
        ]
    if classification == Classification.UNSUPPORTED_MODEL_FEATURE:
        return ["model uses a feature outside the current OR-CI Gurobi support surface"]
    return []
