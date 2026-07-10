from __future__ import annotations

import json
from pathlib import Path

import pytest

from or_ci.benchmark_audit_cli import main
from or_ci.nl4opt_audit import (
    answers_equal,
    build_target_model,
    map_benchmark_rows,
    parse_number,
    read_jsonl,
    result_matches_answer,
    solve_target,
    validate_source_manifest,
)


def _payload(document: str, *, limit: str = "10") -> dict:
    return {
        "document": document,
        "vars": ["alpha units", "beta units"],
        "var_mention_to_first_var": {
            "alpha": "alpha units",
            "beta": "beta units",
        },
        "obj_declaration": {
            "type": "objective",
            "direction": "maximize",
            "name": "value",
            "terms": {"alpha": "two", "beta": "1"},
        },
        "const_declarations": [
            {
                "type": "linear",
                "direction": "capacity",
                "limit": limit,
                "terms": {"alpha": "1", "beta": "1"},
                "operator": "LESS_OR_EQUAL",
            },
            {"type": "sum", "direction": "capacity", "limit": "12", "operator": "LESS_OR_EQUAL"},
            {
                "type": "lowerbound",
                "direction": "at least",
                "limit": "2",
                "var": "alpha",
                "operator": "GREATER_OR_EQUAL",
            },
            {
                "type": "upperbound",
                "direction": "at most",
                "limit": "5",
                "var": "beta",
                "operator": "LESS_OR_EQUAL",
            },
            {
                "type": "xy",
                "direction": "at least",
                "x_var": "alpha",
                "y_var": "beta",
                "operator": "GREATER_OR_EQUAL",
            },
            {
                "type": "xby",
                "direction": "at most",
                "param": "twice",
                "x_var": "alpha",
                "y_var": "beta",
                "operator": "LESS_OR_EQUAL",
            },
            {
                "type": "ratio",
                "direction": "at least",
                "limit": "20%",
                "var": "beta",
                "operator": "GREATER_OR_EQUAL",
            },
        ],
    }


@pytest.mark.parametrize(
    ("raw", "ratio", "expected"),
    [
        ("1,500", False, 1500.0),
        ("fifteen", False, 15.0),
        ("twice", False, 2.0),
        ("1.5 times", False, 1.5),
        ("3%", False, 0.03),
        ("third", True, 1.0 / 3.0),
        ("35 percent", True, 0.35),
        ("5", True, 0.05),
    ],
)
def test_parse_number_handles_official_nl4opt_forms(raw: str, ratio: bool, expected: float) -> None:
    assert parse_number(raw, ratio=ratio) == pytest.approx(expected)


def test_build_and_solve_target_supports_all_constraint_shapes() -> None:
    model, variables = build_target_model(_payload("Example"), domain="integer")
    assert len(variables) == 2
    assert model.NumConstrs == 7

    result = solve_target(_payload("Example"), domain="integer")

    assert result["status"] == "optimal"
    assert result["objective"] == pytest.approx(16.0)
    assert result["max_constraint_violation"] <= 1e-7


def test_solve_target_records_iis_for_infeasible_model() -> None:
    payload = _payload("Infeasible", limit="1")
    result = solve_target(payload, domain="continuous")
    assert result["status"] == "infeasible"
    assert result["iis_constraints"]


def test_answer_comparison_normalizes_sentinels_and_numbers() -> None:
    assert answers_equal("-99999.0", "No Best Solution")
    assert answers_equal("1,200", "1200.0")
    assert not answers_equal("2", "3")


def test_result_matching_normalizes_solver_status_case_without_accepting_closure_labels() -> None:
    assert result_matches_answer({"status": "OPTIMAL", "objective": 5.0}, "5")
    assert result_matches_answer({"status": "INFEASIBLE", "objective": None}, "No Best Solution")
    assert result_matches_answer(
        {"status": "STRICT_INEQUALITY_INFIMUM_NOT_ATTAINED", "objective": 5.0},
        "No Best Solution",
    )
    assert not result_matches_answer(
        {"status": "OPTIMAL_CLOSURE_RELAXATION_STRICT_SOURCE_UNRESOLVED", "objective": 5.0},
        "5",
    )


def test_mapping_uses_corrected_question_and_manual_override() -> None:
    from or_ci.nl4opt_audit import OfficialTarget

    official = [
        OfficialTarget("a", _payload("Alpha source statement")),
        OfficialTarget("b", _payload("Beta source statement")),
    ]
    historical = [
        {"en_question": "Alpha source statement", "en_answer": "1"},
        {"en_question": "incomplete", "en_answer": "2"},
    ]
    corrected = [
        {"en_question": "Alpha source statement", "en_answer": "1"},
        {"en_question": "Beta source statement", "en_answer": "3"},
    ]

    mappings = map_benchmark_rows(historical, corrected, official, overrides={"1": "b"})

    assert [row["source_id"] for row in mappings] == ["a", "b"]
    assert mappings[1]["manual_override"] is True


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_prepare_keeps_selection_and_answers_outside_runner_manifest(tmp_path: Path) -> None:
    official_path = tmp_path / "official.jsonl"
    historical_path = tmp_path / "historical.jsonl"
    corrected_path = tmp_path / "corrected.jsonl"
    out_dir = tmp_path / "campaign"
    official_rows = [
        {"source-a": _payload("Alpha exact source")},
        {"source-b": _payload("Beta exact source")},
        {"source-c": _payload("Gamma exact source")},
    ]
    historical_rows = [
        {"en_question": "Alpha exact source", "en_answer": "-99999.0"},
        {"en_question": "Beta exact source", "en_answer": "2"},
        {"en_question": "Gamma exact source", "en_answer": "3"},
    ]
    corrected_rows = [
        {"en_question": "Alpha exact source", "en_answer": "No Best Solution"},
        {"en_question": "Beta exact source", "en_answer": "2"},
        {"en_question": "Gamma exact source", "en_answer": "3"},
    ]
    _write_jsonl(official_path, official_rows)
    _write_jsonl(historical_path, historical_rows)
    _write_jsonl(corrected_path, corrected_rows)

    exit_code = main(
        [
            "prepare-nl4opt",
            "--official",
            str(official_path),
            "--historical",
            str(historical_path),
            "--corrected",
            str(corrected_path),
            "--official-commit",
            "official-sha",
            "--corrected-commit",
            "corrected-sha",
            "--out-dir",
            str(out_dir),
            "--control-count",
            "1",
            "--expected-answer-changes",
            "1",
        ]
    )

    assert exit_code == 0
    manifest_path = out_dir / "source" / "evidence-source-manifest.jsonl"
    manifest = read_jsonl(manifest_path)
    assert len(manifest) == 2
    assert all(set(row) == {"row_id", "split", "statement_path", "source_sha256"} for row in manifest)
    assert {row["split"] for row in manifest} == {"pilot_evidence"}
    assert "answer" not in manifest_path.read_text(encoding="utf-8").lower()
    hidden = read_jsonl(out_dir / "hidden" / "answer-key.jsonl")
    assert {row["selection_group"] for row in hidden} == {"answer_changed", "unchanged_control"}
    validation = validate_source_manifest(manifest_path, out_dir)
    assert validation["status"] == "valid"


def test_source_manifest_validator_rejects_extra_answer_field(tmp_path: Path) -> None:
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    statement = source_dir / "row.txt"
    statement.write_text("Source statement\n", encoding="utf-8")
    from or_ci.nl4opt_audit import sha256_file

    manifest = source_dir / "manifest.jsonl"
    _write_jsonl(
        manifest,
        [
            {
                "row_id": "row-1",
                "split": "pilot_evidence",
                "statement_path": "source/row.txt",
                "source_sha256": sha256_file(statement),
                "answer": "hidden",
            }
        ],
    )

    result = validate_source_manifest(manifest, tmp_path)

    assert result["status"] == "invalid"
    assert "extra fields" in result["errors"][0]
