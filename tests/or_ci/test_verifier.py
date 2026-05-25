from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from or_ci.contracts import Classification
from or_ci.verifier import verify

BWOR_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "bwor"


def _write_problem(path) -> None:
    path.write_text(
        json.dumps(
            {
                "id": "BWOR-FAKE",
                "problem_type": "LP",
                "instance": {"price": 3.0},
                "metamorphic": {
                    "cost_scaling": {
                        "coefficient_paths": ["instance.price"],
                        "factors": [2.0],
                        "tolerance_abs": 1e-6,
                        "tolerance_rel": 1e-6,
                    }
                },
                "evaluation_only": {"answer": 999.0, "label": "must_not_be_passed"},
            }
        ),
        encoding="utf-8",
    )


def _write_fake_submission(path, objective_expression: str) -> None:
    path.write_text(
        f"""
from gurobipy import GRB


class FakeModel:
    def __init__(self, objective):
        self.Status = GRB.OPTIMAL
        self.ObjVal = objective

    def setParam(self, *args):
        pass

    def optimize(self):
        pass


def build_model(data):
    if "evaluation_only" in data or "answer" in data or "label" in data:
        raise RuntimeError("evaluation_only leaked into build_model")
    return FakeModel({objective_expression})
""",
        encoding="utf-8",
    )


def _qp_problem() -> dict:
    return {
        "id": "BWOR-067",
        "problem_type": "QP",
        "instance": {"quad_coeff": 1.0},
        "metamorphic": {
            "cost_scaling": {
                "coefficient_paths": ["instance.quad_coeff"],
                "factors": [2.0],
                "tolerance_abs": 1e-6,
                "tolerance_rel": 1e-6,
            }
        },
    }


def _write_qp_problem(path: Path) -> None:
    path.write_text(json.dumps(_qp_problem()), encoding="utf-8")


def _write_qp_submission(path: Path, coefficient_expression: str) -> None:
    path.write_text(
        f"""
import gurobipy as gp
from gurobipy import GRB


def build_model(data):
    model = gp.Model()
    x = model.addVar(name="x", lb=0.0)
    model.addConstr(x == 2.0, name="fix_x")
    model.setObjective(({coefficient_expression}) * x * x, GRB.MINIMIZE)
    return model
""",
        encoding="utf-8",
    )


def _write_weighted_goal_problem(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "id": "BWOR-014",
                "problem_type": "LP",
                "instance": {"weights": {"profit": 3.0, "risk": 1.0}},
                "metamorphic": {
                    "cost_scaling": {
                        "coefficient_paths": ["instance.weights"],
                        "factors": [2.0],
                    },
                    "goal_programming": {
                        "mode": "weighted",
                        "objective_sense": "min",
                        "goals": [
                            {
                                "name": "profit_deviation",
                                "expression": {"variables": {"d_profit": 1.0}},
                                "weight": 3.0,
                            },
                            {
                                "name": "risk_deviation",
                                "expression": {"variables": {"d_risk": 1.0}},
                                "weight": 1.0,
                            },
                        ],
                    },
                },
            }
        ),
        encoding="utf-8",
    )


def _write_lexicographic_goal_problem(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "id": "BWOR-015",
                "problem_type": "LP",
                "instance": {"priority_weights": {"p1": 100.0, "p2": 1.0}},
                "metamorphic": {
                    "cost_scaling": {
                        "coefficient_paths": ["instance.priority_weights"],
                        "factors": [2.0],
                    },
                    "goal_programming": {
                        "mode": "lexicographic",
                        "objective_sense": "min",
                        "goals": [
                            {
                                "name": "priority_1",
                                "expression": {"variables": {"d1": 1.0}},
                                "priority": 1,
                                "priority_weight": 100.0,
                            },
                            {
                                "name": "priority_2",
                                "expression": {"variables": {"d2": 1.0}},
                                "priority": 2,
                                "priority_weight": 1.0,
                            },
                        ],
                    },
                },
            }
        ),
        encoding="utf-8",
    )


def _write_goal_submission(path: Path, *, mode: str, wrong_order: bool) -> None:
    if mode == "weighted":
        weight_source = "data['weights']"
        first_coeff = f"{weight_source}['profit']"
        second_coeff = f"{weight_source}['risk']"
        first_var = "d_profit"
        second_var = "d_risk"
    else:
        weight_source = "data['priority_weights']"
        if wrong_order:
            first_coeff = f"{weight_source}['p2']"
            second_coeff = f"{weight_source}['p1']"
        else:
            first_coeff = f"{weight_source}['p1']"
            second_coeff = f"{weight_source}['p2']"
        first_var = "d1"
        second_var = "d2"

    path.write_text(
        f"""
from gurobipy import GRB


class Var:
    def __init__(self, name, value):
        self.VarName = name
        self.LB = 0.0
        self.UB = GRB.INFINITY
        self.VType = GRB.CONTINUOUS
        self.X = value


class Expr:
    def __init__(self, terms):
        self.terms = terms

    def size(self):
        return len(self.terms)

    def getVar(self, index):
        return self.terms[index][0]

    def getCoeff(self, index):
        return self.terms[index][1]

    def getConstant(self):
        return 0.0


class Constr:
    ConstrName = "goal_balance"
    Sense = "="
    RHS = 1.0

    def __init__(self, row):
        self.row = row


class FakeModel:
    NumSOS = 0
    NumQConstrs = 0
    NumGenConstrs = 0
    NumPWLObjVars = 0
    NumQNZs = 0
    IsMultiObj = 0
    ModelSense = GRB.MINIMIZE
    Status = GRB.OPTIMAL

    def __init__(self, first_coeff, second_coeff):
        self.v1 = Var("{first_var}", 2.0)
        self.v2 = Var("{second_var}", 5.0)
        self.ObjVal = first_coeff * self.v1.X + second_coeff * self.v2.X
        self.objective = Expr([(self.v1, first_coeff), (self.v2, second_coeff)])
        self.constraint = Constr(Expr([(self.v1, 1.0)]))

    def update(self):
        pass

    def getVars(self):
        return [self.v1, self.v2]

    def getConstrs(self):
        return [self.constraint]

    def getRow(self, constr):
        return constr.row

    def getObjective(self):
        return self.objective

    def setParam(self, *args):
        pass

    def optimize(self):
        pass


def build_model(data):
    return FakeModel({first_coeff}, {second_coeff})
""",
        encoding="utf-8",
    )


def _write_multi_scenario_problem(path: Path, *, base_required: bool = True) -> None:
    path.write_text(
        json.dumps(
            {
                "id": "BWOR-032",
                "problem_type": "MULTI_SCENARIO",
                "scenarios": [
                    {
                        "name": "base_infeasible",
                        "instance": {"case": "base", "objective": 0.0},
                        "expected_solver_status": "INFEASIBLE",
                        "required": base_required,
                    },
                    {
                        "name": "rental_feasible",
                        "instance": {"case": "rental", "objective": 10.0},
                        "expected_solver_status": "OPTIMAL",
                        "objective": {"value": 10.0},
                        "metamorphic": {
                            "cost_scaling": {
                                "coefficient_paths": ["instance.objective"],
                                "factors": [2.0],
                            }
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_scenario_submission(path: Path, *, force_wrong_status: bool) -> None:
    status_expression = "GRB.OPTIMAL" if force_wrong_status else "GRB.INFEASIBLE"
    path.write_text(
        f"""
from gurobipy import GRB


class Var:
    VarName = "x"
    LB = 0.0
    UB = GRB.INFINITY
    VType = GRB.CONTINUOUS
    X = 1.0


class Expr:
    def __init__(self, coeff):
        self.var = Var()
        self.coeff = coeff

    def size(self):
        return 1

    def getVar(self, index):
        return self.var

    def getCoeff(self, index):
        return self.coeff

    def getConstant(self):
        return 0.0


class Constr:
    ConstrName = "fix_x"
    Sense = "="
    RHS = 1.0

    def __init__(self, row):
        self.row = row


class FakeModel:
    NumSOS = 0
    NumQConstrs = 0
    NumGenConstrs = 0
    NumPWLObjVars = 0
    NumQNZs = 0
    IsMultiObj = 0
    ModelSense = GRB.MINIMIZE

    def __init__(self, data):
        self.x = Var()
        self.objective = Expr(data["objective"])
        self.constraint = Constr(Expr(1.0))
        if data["case"] == "base":
            self.Status = {status_expression}
            self.ObjVal = 0.0
        else:
            self.Status = GRB.OPTIMAL
            self.ObjVal = data["objective"]

    def update(self):
        pass

    def getVars(self):
        return [self.x]

    def getConstrs(self):
        return [self.constraint]

    def getRow(self, constr):
        return constr.row

    def getObjective(self):
        return self.objective

    def setParam(self, *args):
        pass

    def optimize(self):
        pass


def build_model(data):
    return FakeModel(data)
""",
        encoding="utf-8",
    )


def test_verifier_passes_only_instance_and_classifies_success(tmp_path, monkeypatch) -> None:
    problem_path = tmp_path / "problem.json"
    submission_path = tmp_path / "submission.py"
    _write_problem(problem_path)
    _write_fake_submission(submission_path, "data['price']")
    monkeypatch.setattr(
        "or_ci.verifier.extract_model_ir",
        lambda model: SimpleNamespace(summary={"variables": 1}, objective=SimpleNamespace(quadratic_terms=[])),
    )

    report = verify(problem_path, submission_path)

    assert report.classification == Classification.SUCCESS
    assert report.status.value == "PASS"
    assert report.failures == []


def test_verifier_classifies_cost_scaling_failure(tmp_path, monkeypatch) -> None:
    problem_path = tmp_path / "problem.json"
    submission_path = tmp_path / "submission.py"
    _write_problem(problem_path)
    _write_fake_submission(submission_path, "10.0")
    monkeypatch.setattr(
        "or_ci.verifier.extract_model_ir",
        lambda model: SimpleNamespace(summary={"variables": 1}, objective=SimpleNamespace(quadratic_terms=[])),
    )

    report = verify(problem_path, submission_path)

    assert report.classification == Classification.RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL
    assert report.failures[0]["check"] == "cost_scaling"


@pytest.mark.parametrize("problem_id", ["BWOR-001", "BWOR-002", "BWOR-010"])
def test_runtime_error_fixtures_classify_as_syntax_or_runtime(problem_id: str) -> None:
    report = verify(
        BWOR_FIXTURES / problem_id / "problem.json",
        BWOR_FIXTURES / problem_id / "runtime_error.py",
    )

    assert report.classification == Classification.SYNTAX_OR_RUNTIME_ERROR


@pytest.mark.parametrize("problem_id", ["BWOR-001", "BWOR-002", "BWOR-010"])
def test_correct_bwor_fixtures_classify_success(problem_id: str, require_gurobi_license) -> None:
    report = verify(
        BWOR_FIXTURES / problem_id / "problem.json",
        BWOR_FIXTURES / problem_id / "correct.py",
    )

    assert report.classification == Classification.SUCCESS
    assert report.model_ir_summary["variables"] > 0
    assert report.model_ir_summary["constraints"] > 0


@pytest.mark.parametrize("problem_id", ["BWOR-001", "BWOR-002", "BWOR-010"])
def test_wrong_bwor_fixtures_classify_semantic_failure(problem_id: str, require_gurobi_license) -> None:
    report = verify(
        BWOR_FIXTURES / problem_id / "problem.json",
        BWOR_FIXTURES / problem_id / "wrong.py",
    )

    assert report.classification == Classification.RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL
    assert report.failures[0]["check"] == "cost_scaling"


@pytest.mark.parametrize("problem_id", ["BWOR-001", "BWOR-002", "BWOR-010"])
def test_wrong_constraint_bwor_fixtures_classify_semantic_failure(problem_id: str, require_gurobi_license) -> None:
    report = verify(
        BWOR_FIXTURES / problem_id / "problem.json",
        BWOR_FIXTURES / problem_id / "wrong_constraint.py",
    )

    assert report.classification == Classification.RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL
    assert any(check.name == "cost_scaling" and check.status == "PASS" for check in report.checks)
    assert report.failures[0]["check"] == "constraint_relaxation"


def test_qp_cost_scaling_classifies_success(tmp_path, require_gurobi_license) -> None:
    problem_path = tmp_path / "problem.json"
    submission_path = tmp_path / "submission.py"
    _write_qp_problem(problem_path)
    _write_qp_submission(submission_path, "data['quad_coeff']")

    report = verify(problem_path, submission_path)

    assert report.classification == Classification.SUCCESS
    assert report.model_ir_summary["quadratic_objective_terms"] == 1
    assert any(check.name == "cost_scaling" and check.status == "PASS" for check in report.checks)


def test_qp_cost_scaling_classifies_wrong_objective(tmp_path, require_gurobi_license) -> None:
    problem_path = tmp_path / "problem.json"
    submission_path = tmp_path / "submission.py"
    _write_qp_problem(problem_path)
    _write_qp_submission(submission_path, "1.0")

    report = verify(problem_path, submission_path)

    assert report.classification == Classification.RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL
    assert report.failures[0]["check"] == "cost_scaling"


def test_quadratic_objective_requires_qp_problem_type(tmp_path, require_gurobi_license) -> None:
    problem_path = tmp_path / "problem.json"
    submission_path = tmp_path / "submission.py"
    problem = _qp_problem()
    problem["problem_type"] = "LP"
    problem_path.write_text(json.dumps(problem), encoding="utf-8")
    _write_qp_submission(submission_path, "data['quad_coeff']")

    report = verify(problem_path, submission_path)

    assert report.classification == Classification.UNSUPPORTED_MODEL_FEATURE
    assert "problem_type QP or MIQP" in report.failures[0]["message"]


def test_quadratic_constraints_remain_unsupported(tmp_path, require_gurobi_license) -> None:
    problem_path = tmp_path / "problem.json"
    submission_path = tmp_path / "submission.py"
    _write_qp_problem(problem_path)
    submission_path.write_text(
        """
import gurobipy as gp
from gurobipy import GRB


def build_model(data):
    model = gp.Model()
    x = model.addVar(name="x", lb=0.0)
    model.addQConstr(x * x <= 1.0, name="q_constr")
    model.setObjective(data["quad_coeff"] * x * x, GRB.MINIMIZE)
    return model
""",
        encoding="utf-8",
    )

    report = verify(problem_path, submission_path)

    assert report.classification == Classification.UNSUPPORTED_MODEL_FEATURE
    assert "quadratic constraints" in report.failures[0]["message"]


def test_weighted_goal_programming_classifies_success(tmp_path) -> None:
    problem_path = tmp_path / "problem.json"
    submission_path = tmp_path / "submission.py"
    _write_weighted_goal_problem(problem_path)
    _write_goal_submission(submission_path, mode="weighted", wrong_order=False)

    report = verify(problem_path, submission_path)

    assert report.classification == Classification.SUCCESS
    goal_check = next(check for check in report.checks if check.name == "goal_programming")
    assert goal_check.details["goal_values"][0]["name"] == "profit_deviation"


def test_lexicographic_goal_programming_detects_wrong_priority_order(tmp_path) -> None:
    problem_path = tmp_path / "problem.json"
    submission_path = tmp_path / "submission.py"
    _write_lexicographic_goal_problem(problem_path)
    _write_goal_submission(submission_path, mode="lexicographic", wrong_order=True)

    report = verify(problem_path, submission_path)

    assert report.classification == Classification.RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL
    assert report.failures[0]["check"] == "goal_programming"
    assert report.failures[0]["coefficient_differences"]


def test_multi_scenario_verification_classifies_success(tmp_path) -> None:
    problem_path = tmp_path / "problem.json"
    submission_path = tmp_path / "submission.py"
    _write_multi_scenario_problem(problem_path)
    _write_scenario_submission(submission_path, force_wrong_status=False)

    report = verify(problem_path, submission_path)

    assert report.classification == Classification.SUCCESS
    assert report.model_ir_summary["scenarios"] == 2
    assert any(check.name == "scenario_solver_status" and check.status == "PASS" for check in report.checks)
    assert any(check.name == "scenario_cost_scaling" and check.status == "PASS" for check in report.checks)


def test_multi_scenario_wrong_status_fails_aggregate(tmp_path) -> None:
    problem_path = tmp_path / "problem.json"
    submission_path = tmp_path / "submission.py"
    _write_multi_scenario_problem(problem_path)
    _write_scenario_submission(submission_path, force_wrong_status=True)

    report = verify(problem_path, submission_path)

    assert report.classification == Classification.SOLVER_STATUS_ERROR
    assert report.failures[0]["check"] == "scenario_solver_status"


def test_multi_scenario_optional_wrong_status_does_not_fail_aggregate(tmp_path) -> None:
    problem_path = tmp_path / "problem.json"
    submission_path = tmp_path / "submission.py"
    _write_multi_scenario_problem(problem_path, base_required=False)
    _write_scenario_submission(submission_path, force_wrong_status=True)

    report = verify(problem_path, submission_path)

    assert report.classification == Classification.SUCCESS
    assert report.status.value == "PASS"
    assert report.model_ir_summary["required_scenarios"] == 1
    assert any(
        check.name == "scenario_solver_status"
        and check.status == "FAIL"
        and check.details["scenario"] == "base_infeasible"
        and check.details["required"] is False
        for check in report.checks
    )
    assert report.failures[0]["check"] == "scenario_solver_status"
    assert report.failures[0]["required"] is False
