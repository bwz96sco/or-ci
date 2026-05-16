from __future__ import annotations

import copy
import math
from pathlib import Path
from typing import Any

from gurobipy import GRB

from or_ci.contracts import (
    CheckResult,
    Classification,
    ProblemMetadata,
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
        original_model = build_model(copy.deepcopy(problem.instance))
        model_ir = extract_model_ir(original_model)
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
        classification = _run_cost_scaling_checks(
            problem,
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
            problem,
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


def _run_cost_scaling_checks(
    problem: ProblemMetadata,
    build_model: Any,
    original_obj: float,
    solver_status: dict[str, Any],
    checks: list[CheckResult],
    failures: list[dict[str, Any]],
) -> Classification | None:
    for factor in problem.cost_scaling.factors:
        scaled_data = scaled_instance(problem.instance, problem.cost_scaling, factor)
        scaled_model = build_model(scaled_data)
        scaled_result = _optimize(scaled_model)
        solver_status[f"scaled_{factor:g}"] = scaled_result
        if not scaled_result["is_optimal"]:
            checks.append(
                CheckResult(
                    name="cost_scaling",
                    status="FAIL",
                    details={"factor": factor, "scaled_solver_status": scaled_result},
                )
            )
            failures.append(
                {
                    "check": "cost_scaling",
                    "message": "scaled model did not solve to optimality",
                    "factor": factor,
                    "observed_status": scaled_result,
                }
            )
            return Classification.SOLVER_STATUS_ERROR

        scaled_obj = float(scaled_result["objective_value"])
        expected_obj = factor * original_obj
        passed = math.isclose(
            scaled_obj,
            expected_obj,
            rel_tol=problem.cost_scaling.tolerance_rel,
            abs_tol=problem.cost_scaling.tolerance_abs,
        )
        details = {
            "factor": factor,
            "original_objective": original_obj,
            "scaled_objective": scaled_obj,
            "expected_scaled_objective": expected_obj,
            "tolerance_abs": problem.cost_scaling.tolerance_abs,
            "tolerance_rel": problem.cost_scaling.tolerance_rel,
            "expected_relation": "scaled_obj ~= factor * original_obj",
        }
        checks.append(CheckResult(name="cost_scaling", status="PASS" if passed else "FAIL", details=details))
        if not passed:
            failures.append(
                {
                    "check": "cost_scaling",
                    "message": "scaled objective did not match the cost-scaling invariant",
                    **details,
                }
            )
            return Classification.RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL
    return None


def _run_constraint_relaxation_checks(
    problem: ProblemMetadata,
    build_model: Any,
    original_obj: float,
    solver_status: dict[str, Any],
    checks: list[CheckResult],
    failures: list[dict[str, Any]],
) -> Classification | None:
    if problem.constraint_relaxation is None:
        return None

    for relaxation in problem.constraint_relaxation.relaxations:
        relaxed_data = scale_numeric_paths(
            problem.instance,
            relaxation.paths,
            relaxation.factor,
            context="constraint-relaxation",
        )
        relaxed_model = build_model(relaxed_data)
        relaxed_result = _optimize(relaxed_model)
        status_key = f"relaxed_{relaxation.name}"
        solver_status[status_key] = relaxed_result
        if not relaxed_result["is_optimal"]:
            checks.append(
                CheckResult(
                    name="constraint_relaxation",
                    status="FAIL",
                    details={"relaxation": relaxation.name, "relaxed_solver_status": relaxed_result},
                )
            )
            failures.append(
                {
                    "check": "constraint_relaxation",
                    "message": "relaxed model did not solve to optimality",
                    "relaxation": relaxation.name,
                    "observed_status": relaxed_result,
                }
            )
            return Classification.SOLVER_STATUS_ERROR

        relaxed_obj = float(relaxed_result["objective_value"])
        passed = _objective_relation_holds(
            original_obj,
            relaxed_obj,
            relaxation.objective_relation,
            problem.constraint_relaxation.tolerance_abs,
            problem.constraint_relaxation.tolerance_rel,
        )
        details = {
            "relaxation": relaxation.name,
            "paths": relaxation.paths,
            "factor": relaxation.factor,
            "original_objective": original_obj,
            "relaxed_objective": relaxed_obj,
            "objective_relation": relaxation.objective_relation,
            "tolerance_abs": problem.constraint_relaxation.tolerance_abs,
            "tolerance_rel": problem.constraint_relaxation.tolerance_rel,
        }
        checks.append(
            CheckResult(name="constraint_relaxation", status="PASS" if passed else "FAIL", details=details)
        )
        if not passed:
            failures.append(
                {
                    "check": "constraint_relaxation",
                    "message": "relaxed objective did not satisfy the configured relation",
                    **details,
                }
            )
            return Classification.RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL
    return None


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
        return ["original or scaled model did not solve to optimal status"]
    if classification == Classification.RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL:
        return [
            "objective coefficients may not use the configured coefficient paths",
            "constraints may not use the configured relaxation paths",
            "objective sign or constant terms may be wrong",
            "the model may be optimizing a different objective from the metadata",
        ]
    if classification == Classification.UNSUPPORTED_MODEL_FEATURE:
        return ["model uses a feature outside Phase 1 linear Gurobi support"]
    return []
