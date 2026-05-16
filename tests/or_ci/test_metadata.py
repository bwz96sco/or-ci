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
