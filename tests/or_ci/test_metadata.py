from __future__ import annotations

import json
from pathlib import Path

import pytest

from or_ci.metadata import MetadataError, load_problem_metadata
from or_ci.scaling import scale_numeric_paths, scaled_instance

BWOR_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "bwor"


def test_metadata_loader_accepts_fixture() -> None:
    metadata = load_problem_metadata(BWOR_FIXTURES / "BWOR-002" / "problem.json")

    assert metadata.id == "BWOR-002"
    assert metadata.problem_type == "LP"
    assert metadata.cost_scaling.coefficient_paths == ["instance.price"]
    assert metadata.constraint_relaxation is not None
    assert metadata.constraint_relaxation.relaxations[0].name == "requirements_decrease"
    assert metadata.constraint_relaxation.relaxations[0].paths == ["instance.requirements"]
    assert metadata.constraint_relaxation.relaxations[0].factor == 0.9
    assert metadata.constraint_relaxation.relaxations[0].objective_relation == "decrease"
    assert metadata.evaluation_only["answer"] == 32.43


def test_metadata_loader_accepts_qp_problem_type(tmp_path) -> None:
    problem_path = tmp_path / "problem.json"
    problem = _minimal_problem()
    problem["problem_type"] = "QP"
    problem_path.write_text(json.dumps(problem), encoding="utf-8")

    metadata = load_problem_metadata(problem_path)

    assert metadata.problem_type == "QP"


def test_metadata_loader_accepts_weighted_goal_programming(tmp_path) -> None:
    problem_path = tmp_path / "problem.json"
    problem = _minimal_problem()
    problem["metamorphic"]["goal_programming"] = {
        "mode": "weighted",
        "objective_sense": "min",
        "goals": [
            {
                "name": "profit_deviation",
                "expression": {"variables": {"d_profit": 1.0}},
                "weight": 3.0,
            }
        ],
    }
    problem_path.write_text(json.dumps(problem), encoding="utf-8")

    metadata = load_problem_metadata(problem_path)

    assert metadata.goal_programming is not None
    assert metadata.goal_programming.mode == "weighted"
    assert metadata.goal_programming.goals[0].weight == 3.0


def test_metadata_loader_accepts_lexicographic_goal_programming(tmp_path) -> None:
    problem_path = tmp_path / "problem.json"
    problem = _minimal_problem()
    problem["metamorphic"]["goal_programming"] = {
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
    }
    problem_path.write_text(json.dumps(problem), encoding="utf-8")

    metadata = load_problem_metadata(problem_path)

    assert metadata.goal_programming is not None
    assert metadata.goal_programming.mode == "lexicographic"
    assert [goal.priority for goal in metadata.goal_programming.goals] == [1, 2]


def test_metadata_loader_rejects_weighted_goal_without_weight(tmp_path) -> None:
    problem_path = tmp_path / "problem.json"
    problem = _minimal_problem()
    problem["metamorphic"]["goal_programming"] = {
        "mode": "weighted",
        "objective_sense": "min",
        "goals": [
            {
                "name": "profit_deviation",
                "expression": {"variables": {"d_profit": 1.0}},
            }
        ],
    }
    problem_path.write_text(json.dumps(problem), encoding="utf-8")

    with pytest.raises(MetadataError, match="weight must be a positive number"):
        load_problem_metadata(problem_path)


def test_metadata_loader_rejects_lexicographic_goal_priority_weight_order(tmp_path) -> None:
    problem_path = tmp_path / "problem.json"
    problem = _minimal_problem()
    problem["metamorphic"]["goal_programming"] = {
        "mode": "lexicographic",
        "objective_sense": "min",
        "goals": [
            {
                "name": "priority_1",
                "expression": {"variables": {"d1": 1.0}},
                "priority": 1,
                "priority_weight": 1.0,
            },
            {
                "name": "priority_2",
                "expression": {"variables": {"d2": 1.0}},
                "priority": 2,
                "priority_weight": 100.0,
            },
        ],
    }
    problem_path.write_text(json.dumps(problem), encoding="utf-8")

    with pytest.raises(MetadataError, match="priority_weight values must strictly decrease"):
        load_problem_metadata(problem_path)


def test_metadata_loader_accepts_multi_scenario_problem(tmp_path) -> None:
    problem_path = tmp_path / "problem.json"
    problem = {
        "id": "BWOR-SCENARIO",
        "problem_type": "MULTI_SCENARIO",
        "scenarios": [
            {
                "name": "base",
                "instance": {"objective": 1.0},
                "expected_solver_status": "INFEASIBLE",
            },
            {
                "name": "repair",
                "instance": {"objective": 2.0},
                "expected_solver_status": "OPTIMAL",
                "objective": {"value": 2.0},
                "metamorphic": {
                    "cost_scaling": {
                        "coefficient_paths": ["instance.objective"],
                        "factors": [2.0],
                    }
                },
            },
        ],
    }
    problem_path.write_text(json.dumps(problem), encoding="utf-8")

    metadata = load_problem_metadata(problem_path)

    assert metadata.scenarios[0].expected_solver_status == "INFEASIBLE"
    assert metadata.scenarios[1].objective_check is not None
    assert metadata.scenarios[1].cost_scaling is not None


def test_metadata_loader_rejects_missing_required_fields(tmp_path) -> None:
    problem_path = tmp_path / "problem.json"
    problem_path.write_text(json.dumps({"id": "BWOR-TEST"}), encoding="utf-8")

    with pytest.raises(MetadataError, match="problem_type is required"):
        load_problem_metadata(problem_path)


def test_scaled_instance_scales_only_configured_numeric_values() -> None:
    metadata = load_problem_metadata(BWOR_FIXTURES / "BWOR-002" / "problem.json")
    scaled = scaled_instance(metadata.instance, metadata.cost_scaling, 2.0)

    assert scaled["price"]["feed_1"] == 0.4
    assert scaled["price"]["feed_5"] == 1.6
    assert scaled["requirements"]["protein"] == 700
    assert metadata.instance["price"]["feed_1"] == 0.2


def test_scale_numeric_paths_scales_constraint_relaxation_paths() -> None:
    metadata = load_problem_metadata(BWOR_FIXTURES / "BWOR-002" / "problem.json")
    relaxed = scale_numeric_paths(
        metadata.instance,
        ["instance.requirements"],
        0.9,
        context="constraint-relaxation",
    )

    assert relaxed["requirements"]["protein"] == 630.0
    assert relaxed["requirements"]["minerals"] == 27.0
    assert relaxed["price"]["feed_1"] == 0.2
    assert metadata.instance["requirements"]["protein"] == 700


def _minimal_problem() -> dict:
    return {
        "id": "BWOR-MIN",
        "problem_type": "LP",
        "instance": {"price": 1.0},
        "metamorphic": {
            "cost_scaling": {
                "coefficient_paths": ["instance.price"],
                "factors": [2.0],
            }
        },
    }
