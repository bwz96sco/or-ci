from __future__ import annotations

import hashlib
import json

import pytest

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
    _write_cli_submission(submission_path)

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


def test_evidence_pack_writes_statement_linked_report(tmp_path) -> None:
    statement_path = tmp_path / "statement.txt"
    problem_path = tmp_path / "problem.json"
    submission_path = tmp_path / "submission.py"
    pack_path = tmp_path / "evidence-pack.json"

    statement = "Minimize price times one fixed unit."
    statement_path.write_text(statement, encoding="utf-8")
    _write_cli_problem(problem_path)
    _write_cli_submission(submission_path)

    exit_code = main(
        [
            "evidence-pack",
            "--statement",
            str(statement_path),
            "--problem",
            str(problem_path),
            "--submission",
            str(submission_path),
            "--out",
            str(pack_path),
        ]
    )

    assert exit_code == 0
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    assert pack["schema_version"] == "or_ci_evidence_pack_v1"
    assert pack["source_statement"]["path"] == str(statement_path)
    assert pack["source_statement"]["sha256"] == hashlib.sha256(statement.encode()).hexdigest()
    assert pack["problem_metadata"]["problem_id"] == "BWOR-CLI"
    assert pack["problem_metadata"]["problem_type"] == "LP"
    assert pack["verification_report"]["classification"] == "SUCCESS"
    assert pack["verification_report"]["status"] == "PASS"
    assert pack["answer_evidence"] == {
        "verification_status": "PASS",
        "classification": "SUCCESS",
        "original_solver_status": {
            "code": 2,
            "is_optimal": True,
            "name": "OPTIMAL",
            "objective_value": 4.0,
        },
        "original_objective_value": 4.0,
        "answer_available": True,
        "answer_source": "verification_report.solver_status.original.objective_value",
    }
    assert "OR-CI PASS is not proof of source-statement correctness." in pack["source_fidelity_boundary"]["non_claims"]


def test_evidence_pack_rejects_missing_statement(tmp_path) -> None:
    problem_path = tmp_path / "problem.json"
    submission_path = tmp_path / "submission.py"
    pack_path = tmp_path / "evidence-pack.json"

    _write_cli_problem(problem_path)
    _write_cli_submission(submission_path)

    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "evidence-pack",
                "--statement",
                str(tmp_path / "missing.txt"),
                "--problem",
                str(problem_path),
                "--submission",
                str(submission_path),
                "--out",
                str(pack_path),
            ]
        )

    assert "statement file does not exist" in str(excinfo.value)
    assert not pack_path.exists()


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


def _write_cli_submission(path) -> None:
    path.write_text(
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
