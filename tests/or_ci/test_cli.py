from __future__ import annotations

import json

from or_ci.cli import main
from or_ci.report import read_report


def test_validate_spec_accepts_valid_problem(tmp_path, capsys) -> None:
    problem_path = tmp_path / "problem.json"
    _write_cli_problem(problem_path)

    exit_code = main(["validate-spec", "--problem", str(problem_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "valid problem metadata: BWOR-CLI" in captured.out


def test_validate_spec_rejects_missing_instance(tmp_path, capsys) -> None:
    problem_path = tmp_path / "problem.json"
    problem = _cli_problem()
    problem.pop("instance")
    problem_path.write_text(json.dumps(problem), encoding="utf-8")

    exit_code = main(["validate-spec", "--problem", str(problem_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "instance is required" in captured.err


def test_validate_spec_rejects_missing_cost_scaling(tmp_path, capsys) -> None:
    problem_path = tmp_path / "problem.json"
    problem = _cli_problem()
    problem["metamorphic"] = {}
    problem_path.write_text(json.dumps(problem), encoding="utf-8")

    exit_code = main(["validate-spec", "--problem", str(problem_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "metamorphic.cost_scaling is required" in captured.err


def test_validate_spec_rejects_invalid_constraint_relaxation(tmp_path, capsys) -> None:
    problem_path = tmp_path / "problem.json"
    problem = _cli_problem()
    problem["metamorphic"]["constraint_relaxation"] = {
        "relaxations": [
            {
                "name": "bad_relation",
                "paths": ["instance.price"],
                "factor": 0.5,
                "objective_relation": "maybe",
            }
        ]
    }
    problem_path.write_text(json.dumps(problem), encoding="utf-8")

    exit_code = main(["validate-spec", "--problem", str(problem_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "objective_relation must be one of" in captured.err


def test_validate_spec_accepts_multi_scenario_problem(tmp_path, capsys) -> None:
    problem_path = tmp_path / "problem.json"
    problem_path.write_text(
        json.dumps(
            {
                "id": "BWOR-SCENARIO",
                "problem_type": "MULTI_SCENARIO",
                "scenarios": [
                    {
                        "name": "base",
                        "instance": {},
                        "expected_solver_status": "INFEASIBLE",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(["validate-spec", "--problem", str(problem_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "valid problem metadata: BWOR-SCENARIO" in captured.out


def test_cli_writes_report_for_valid_submission(tmp_path) -> None:
    problem_path = tmp_path / "problem.json"
    submission_path = tmp_path / "submission.py"
    report_path = tmp_path / "report.json"

    _write_cli_problem(problem_path)
    submission_path.write_text(
        """
from gurobipy import GRB


class Var:
    VarName = "x"
    LB = 0.0
    UB = 1.0
    VType = GRB.CONTINUOUS


class Expr:
    def __init__(self, var, coeff):
        self.var = var
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
    Status = GRB.OPTIMAL

    def __init__(self, price):
        self.x = Var()
        self.ObjVal = price
        self.objective = Expr(self.x, price)
        self.constraint = Constr(Expr(self.x, 1.0))

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
    if "evaluation_only" in data:
        raise RuntimeError("evaluation data was leaked")
    return FakeModel(data["price"])
""",
        encoding="utf-8",
    )

    exit_code = main(["verify", "--problem", str(problem_path), "--submission", str(submission_path), "--out", str(report_path)])

    assert exit_code == 0
    report = read_report(report_path)
    assert report["problem_id"] == "BWOR-CLI"
    assert report["classification"] == "SUCCESS"
    assert set(report) == {
        "problem_id",
        "submission",
        "status",
        "classification",
        "solver_status",
        "model_ir_summary",
        "checks",
        "failures",
        "possible_causes",
    }


def _cli_problem() -> dict:
    return {
        "id": "BWOR-CLI",
        "problem_type": "LP",
        "instance": {"price": 4.0},
        "metamorphic": {
            "cost_scaling": {
                "coefficient_paths": ["instance.price"],
                "factors": [2.0],
                "tolerance_abs": 1e-6,
                "tolerance_rel": 1e-6,
            }
        },
        "evaluation_only": {"answer": 4.0, "label": "not_for_build_model"},
    }


def _write_cli_problem(path) -> None:
    path.write_text(json.dumps(_cli_problem()), encoding="utf-8")
