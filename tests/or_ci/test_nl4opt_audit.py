from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from or_ci.benchmark_audit_cli import main
from or_ci.nl4opt_audit import (
    NL4OPTError,
    answer_encoding,
    answer_relation,
    answers_equal,
    build_owner_review_packet,
    build_target_model,
    compare_model_run,
    map_benchmark_rows,
    parse_number,
    read_jsonl,
    result_matches_answer,
    semantic_answer,
    serialize_mechanisms,
    solver_reports_agree,
    solve_target,
    validate_owner_review_packet,
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
    assert semantic_answer("-99999.0") == "No Best Solution"
    assert answer_encoding("-99999.0") == "sentinel_minus_99999"
    assert answer_relation("-99999.0", "No Best Solution") == "encoding_equivalent"
    assert answer_relation("1", "2") == "semantic_difference"
    assert answer_relation("1", "1") == "unchanged"
    assert answers_equal("1,200", "1200.0")
    assert not answers_equal("2", "3")


def test_result_matching_normalizes_solver_status_case_without_accepting_closure_labels() -> None:
    assert result_matches_answer({"status": "OPTIMAL", "objective": 5.0}, "5")
    assert result_matches_answer({"status": 2, "objective": 5.0}, "5")
    assert result_matches_answer({"status": "INFEASIBLE", "objective": None}, "No Best Solution")
    assert result_matches_answer({"status": 3, "objective": None}, "No Best Solution")
    assert result_matches_answer(
        {"status": "STRICT_INEQUALITY_INFIMUM_NOT_ATTAINED", "objective": 5.0},
        "No Best Solution",
    )
    assert not result_matches_answer(
        {"status": "OPTIMAL_CLOSURE_RELAXATION_STRICT_SOURCE_UNRESOLVED", "objective": 5.0},
        "5",
    )


def test_serialize_mechanisms_handles_strings_and_structured_items() -> None:
    assert serialize_mechanisms(["plain", {"name": "strict_relation", "status": "ambiguous"}]) == (
        'plain;{"name": "strict_relation", "status": "ambiguous"}'
    )


def test_solver_reports_agree_normalizes_status_case() -> None:
    left = {
        "continuous": {"status": "OPTIMAL", "objective": 2.0},
        "integer": {"status": "INFEASIBLE", "objective": None},
    }
    right = {
        "continuous": {"status": "optimal", "objective": 2.0 + 1e-8},
        "integer": {"status": "infeasible", "objective": None},
    }
    assert solver_reports_agree(left, right)


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
        {"en_question": "Beta exact source", "en_answer": "4"},
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
            "2",
            "--expected-answer-changes",
            "1",
        ]
    )

    assert exit_code == 0
    manifest_path = out_dir / "source" / "evidence-source-manifest.jsonl"
    manifest = read_jsonl(manifest_path)
    assert len(manifest) == 3
    assert all(set(row) == {"row_id", "split", "statement_path", "source_sha256"} for row in manifest)
    assert {row["split"] for row in manifest} == {"pilot_evidence"}
    assert "answer" not in manifest_path.read_text(encoding="utf-8").lower()
    hidden = read_jsonl(out_dir / "hidden" / "answer-key.jsonl")
    assert {row["selection_group"] for row in hidden} == {"answer_changed", "unchanged_control"}
    assert {row["answer_relation"] for row in hidden} == {
        "semantic_difference",
        "encoding_equivalent",
        "unchanged",
    }
    provenance = json.loads((out_dir / "provenance" / "provenance.json").read_text(encoding="utf-8"))
    assert provenance["counts"]["answer_changed"] == 1
    assert provenance["counts"]["raw_answer_changed"] == 2
    assert provenance["counts"]["encoding_only_changed"] == 1
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


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_compare_model_run_does_not_count_encoding_change_as_correction(tmp_path: Path) -> None:
    campaign_dir = tmp_path / "campaign"
    run_dir = campaign_dir / "runs" / "terra-evidence"
    row_id = "nl4opt-row-0001"
    for directory in ("hidden", "deterministic", "source"):
        (campaign_dir / directory).mkdir(parents=True)
    _write_jsonl(
        campaign_dir / "hidden" / "answer-key.jsonl",
        [
            {
                "row_id": row_id,
                "selection_group": "answer_changed",
                "historical_answer": "-99999.0",
                "corrected_answer": "No Best Solution",
            }
        ],
    )
    _write_jsonl(
        campaign_dir / "deterministic" / "formal-target-answer-comparison.jsonl",
        [{"row_id": row_id, "formal_target_recovers_correction": False}],
    )
    _write_jsonl(
        campaign_dir / "source" / "evidence-source-manifest.jsonl",
        [{"row_id": row_id}],
    )
    workspace = run_dir / "rows" / row_id
    _write_json(workspace / "run-manifest.json", {"terminal_status": "success"})
    report = {
        "continuous": {"status": "INFEASIBLE", "objective": None},
        "integer": {"status": "INFEASIBLE", "objective": None},
    }
    _write_json(workspace / "parent_solver_report.json", report)
    _write_json(
        workspace / "audit.json",
        {
            "chosen_domain": "both",
            "source_status": "inconsistent",
            "mechanisms": [],
            "material_ambiguities": [],
        },
    )

    row = compare_model_run(campaign_dir=campaign_dir, run_dir=run_dir, role="terra")[0]

    assert row["answer_relation"] == "encoding_equivalent"
    assert row["matches_historical"] is True
    assert row["matches_corrected"] is True
    assert row["correction_reproduced_any_domain"] is False
    assert row["correction_discriminated"] is False
    assert row["supported_discrepancy"] is False


def _owner_review_campaign(
    tmp_path: Path,
    *,
    historical_answer: str = "-99999.0",
    corrected_answer: str = "12",
) -> Path:
    campaign_dir = tmp_path / "campaign"
    row_id = "nl4opt-row-0001"
    statement_path = campaign_dir / "source" / "statements" / f"{row_id}.txt"
    statement_path.parent.mkdir(parents=True)
    statement_path.write_text("Use x units to minimize cost.", encoding="utf-8")
    _write_jsonl(
        campaign_dir / "source" / "sol-source-manifest.jsonl",
        [
            {
                "row_id": row_id,
                "split": "sol_adjudication",
                "statement_path": f"source/statements/{row_id}.txt",
                "source_sha256": "test-sha",
            }
        ],
    )
    comparison = {
        "row_id": row_id,
        "selection_group": "answer_changed",
        "historical_answer": historical_answer,
        "corrected_answer": corrected_answer,
        "source_status": "ambiguous",
        "chosen_domain": "integer",
        "continuous_objective": 10.0,
        "integer_objective": 12.0,
        "mechanisms": ["domain interpretation"],
    }
    (campaign_dir / "comparisons").mkdir()
    _write_jsonl(
        campaign_dir / "comparisons" / "terra-answer-comparison.jsonl",
        [comparison],
    )
    _write_jsonl(
        campaign_dir / "comparisons" / "sol-answer-comparison.jsonl",
        [comparison],
    )
    model = {
        "row_id": row_id,
        "variables": [
            {
                "id": "x",
                "meaning": "number of units",
                "lower_bound": 0,
                "domains_checked": ["continuous", "integer"],
                "source_quote": "Use x units.",
            }
        ],
        "objective": {
            "sense": "minimize",
            "expression": "2*x",
            "source_quote": "minimize cost",
        },
        "constraints": [
            {
                "id": "minimum_units",
                "expression": "x >= 5",
                "source_quote": "Use x units.",
            }
        ],
        "assumptions": [
            {
                "id": "domain",
                "text": "Both domains are checked.",
                "source_quote": "Use x units.",
            }
        ],
        "domain_evidence": {
            "continuous": {"assessment": "possible"},
            "integer": {"assessment": "preferred"},
        },
    }
    report = {
        "continuous": {
            "status": "OPTIMAL",
            "objective": 10.0,
            "variables": {},
        },
        "integer": {
            "status": "OPTIMAL",
            "objective": 12.0,
            "variables": {"x": 6.0},
        },
    }
    for run_name in ("terra-evidence", "sol-adjudication"):
        workspace = campaign_dir / "runs" / run_name / "rows" / row_id
        _write_json(workspace / "problem.json", model)
        _write_json(workspace / "parent_solver_report.json", report)
    return campaign_dir


def test_owner_packet_separates_answer_sources_and_embeds_models(tmp_path: Path) -> None:
    campaign_dir = _owner_review_campaign(tmp_path)

    summary = build_owner_review_packet(campaign_dir=campaign_dir)

    assert summary["status"] == "pending"
    csv_path = campaign_dir / "owner-review" / "owner-review-packet.csv"
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["answer_relation"] == "semantic_difference"
    assert rows[0]["dataset_answer"] == "No Best Solution"
    assert rows[0]["dataset_answer_raw"] == "-99999.0"
    assert rows[0]["dataset_answer_encoding"] == "sentinel_minus_99999"
    assert rows[0]["sirl_revised_answer"] == "12"
    assert rows[0]["sirl_revised_answer_raw"] == "12"
    assert rows[0]["terra_generated_continuous_answer"] == "10.0"
    assert rows[0]["terra_generated_integer_answer"] == "12.0"
    assert "historical_answer" not in rows[0]
    assert "corrected_answer" not in rows[0]
    assert "owner_notes" not in rows[0]

    markdown_path = campaign_dir / "owner-review" / "OWNER_REVIEW.md"
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "SIRL revised snapshot" in markdown
    assert "External revision; not ground truth" in markdown
    assert "-99999 is a no-best-solution sentinel, not an objective value" in markdown
    assert "Repaired answer relation: semantic_difference" in markdown
    assert "### Terra-Generated Mathematical Model" in markdown
    assert "### Sol-Generated Mathematical Model" in markdown
    assert "expression: 2*x" in markdown
    assert "expression: x >= 5" in markdown
    assert "| Terra | continuous | OPTIMAL | 10.0 | not available |" in markdown
    assert "#### owner_decision" in markdown
    assert "#### owner_material" in markdown
    assert "#### owner_mechanism" in markdown
    assert "owner_notes" not in markdown

    markdown = markdown.replace("- [ ] sirl_supported", "- [x] sirl_supported", 1)
    markdown = markdown.replace("- [ ] yes", "- [x] yes", 1)
    markdown = markdown.replace(
        "- [ ] reference_value_or_arithmetic_error",
        "- [x] reference_value_or_arithmetic_error",
        1,
    )
    markdown_path.write_text(markdown, encoding="utf-8")
    validated = validate_owner_review_packet(campaign_dir=campaign_dir)
    assert validated["status"] == "valid_complete"
    assert validated["gate_status"] == "fail"

    build_owner_review_packet(campaign_dir=campaign_dir)
    with csv_path.open(newline="", encoding="utf-8") as handle:
        rebuilt = next(csv.DictReader(handle))
    assert rebuilt["owner_decision"] == "sirl_supported"
    assert rebuilt["owner_material"] == "yes"
    assert rebuilt["owner_mechanism"] == "reference_value_or_arithmetic_error"
    rebuilt_markdown = markdown_path.read_text(encoding="utf-8")
    assert "- [x] sirl_supported" in rebuilt_markdown
    assert "- [x] reference_value_or_arithmetic_error" in rebuilt_markdown


def test_owner_packet_uses_per_row_terra_workspace(tmp_path: Path) -> None:
    campaign_dir = _owner_review_campaign(tmp_path)
    row_id = "nl4opt-row-0001"
    default_workspace = campaign_dir / "runs" / "terra-evidence" / "rows" / row_id
    external_workspace = tmp_path / "reused-july-workspace" / row_id
    external_workspace.parent.mkdir(parents=True)
    default_workspace.rename(external_workspace)
    terra_rows = read_jsonl(campaign_dir / "comparisons" / "terra-answer-comparison.jsonl")
    terra_rows[0]["terra_workspace"] = str(external_workspace.resolve())
    _write_jsonl(campaign_dir / "comparisons" / "terra-answer-comparison.jsonl", terra_rows)

    build_owner_review_packet(campaign_dir=campaign_dir)

    with (campaign_dir / "owner-review" / "owner-review-packet.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        row = next(csv.DictReader(handle))
    assert row["terra_model_path"] == str(external_workspace / "problem.json")


def test_owner_packet_excludes_encoding_equivalent_rows(tmp_path: Path) -> None:
    campaign_dir = _owner_review_campaign(
        tmp_path,
        historical_answer="-99999.0",
        corrected_answer="No Best Solution",
    )

    summary = build_owner_review_packet(campaign_dir=campaign_dir)

    assert summary["rows"] == 0
    assert summary["excluded_encoding_equivalent_rows"] == ["nl4opt-row-0001"]
    csv_path = campaign_dir / "owner-review" / "owner-review-packet.csv"
    with csv_path.open(newline="", encoding="utf-8") as handle:
        assert list(csv.DictReader(handle)) == []
    markdown = (campaign_dir / "owner-review" / "OWNER_REVIEW.md").read_text(encoding="utf-8")
    assert "## nl4opt-row-0001" not in markdown
    assert "Rows where dataset and SIRL values differ only by encoding are excluded" in markdown
    validated = validate_owner_review_packet(campaign_dir=campaign_dir)
    assert validated["excluded_encoding_equivalent_rows"] == ["nl4opt-row-0001"]


def test_owner_markdown_rejects_multiple_selections(tmp_path: Path) -> None:
    campaign_dir = _owner_review_campaign(tmp_path)
    build_owner_review_packet(campaign_dir=campaign_dir)
    markdown_path = campaign_dir / "owner-review" / "OWNER_REVIEW.md"
    markdown = markdown_path.read_text(encoding="utf-8")
    markdown = markdown.replace("- [ ] sirl_supported", "- [x] sirl_supported", 1)
    markdown = markdown.replace("- [ ] dataset_supported", "- [x] dataset_supported", 1)
    markdown_path.write_text(markdown, encoding="utf-8")

    with pytest.raises(NL4OPTError, match="multiple Markdown selections for owner_decision"):
        validate_owner_review_packet(campaign_dir=campaign_dir)


def test_owner_packet_validator_enforces_material_case_gate(tmp_path: Path) -> None:
    campaign_dir = tmp_path / "campaign"
    csv_path = campaign_dir / "owner-review" / "owner-review-packet.csv"
    csv_path.parent.mkdir(parents=True)
    rows = [
        {
            "row_id": "row-1",
            "owner_decision": "sirl_supported",
            "owner_material": "yes",
            "owner_mechanism": "domain_or_integrality_ambiguity",
        },
        {
            "row_id": "row-2",
            "owner_decision": "neither_supported",
            "owner_material": "yes",
            "owner_mechanism": "reference_value_or_arithmetic_error",
        },
        {
            "row_id": "row-3",
            "owner_decision": "sirl_supported",
            "owner_material": "yes",
            "owner_mechanism": "domain_or_integrality_ambiguity",
        },
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    result = validate_owner_review_packet(campaign_dir=campaign_dir)

    assert result["status"] == "valid_complete"
    assert result["gate_status"] == "pass"
    assert result["confirmed_material_answer_fault_count"] == 3
    assert result["confirmed_mechanism_count"] == 2
    assert main(["validate-owner-packet", "--campaign-dir", str(campaign_dir)]) == 0

    rows[0]["owner_mechanism"] = "none"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    invalid = validate_owner_review_packet(campaign_dir=campaign_dir)
    assert invalid["status"] == "invalid"
    assert invalid["gate_status"] == "pending"
    assert invalid["errors"] == ["row-1: owner_material yes requires a non-none mechanism"]
    assert main(["validate-owner-packet", "--campaign-dir", str(campaign_dir)]) == 1
