from __future__ import annotations

import json

from or_ci.cli import main
from or_ci.report import read_report


def test_cli_writes_report_for_valid_submission(tmp_path) -> None:
    problem_path = tmp_path / "problem.json"
    submission_path = tmp_path / "submission.py"
    report_path = tmp_path / "report.json"

    problem_path.write_text(
        json.dumps(
            {
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
        ),
        encoding="utf-8",
    )
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
