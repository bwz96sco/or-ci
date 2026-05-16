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


def test_verifier_passes_only_instance_and_classifies_success(tmp_path, monkeypatch) -> None:
    problem_path = tmp_path / "problem.json"
    submission_path = tmp_path / "submission.py"
    _write_problem(problem_path)
    _write_fake_submission(submission_path, "data['price']")
    monkeypatch.setattr("or_ci.verifier.extract_model_ir", lambda model: SimpleNamespace(summary={"variables": 1}))

    report = verify(problem_path, submission_path)

    assert report.classification == Classification.SUCCESS
    assert report.status.value == "PASS"
    assert report.failures == []


def test_verifier_classifies_cost_scaling_failure(tmp_path, monkeypatch) -> None:
    problem_path = tmp_path / "problem.json"
    submission_path = tmp_path / "submission.py"
    _write_problem(problem_path)
    _write_fake_submission(submission_path, "10.0")
    monkeypatch.setattr("or_ci.verifier.extract_model_ir", lambda model: SimpleNamespace(summary={"variables": 1}))

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
