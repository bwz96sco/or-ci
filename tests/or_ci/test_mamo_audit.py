from __future__ import annotations

import json
from pathlib import Path

import pytest

from or_ci.benchmark_answers import (
    MAMO_EASYLP_ANSWER_POLICY,
    answer_relation,
    answers_equal,
)
from or_ci.mamo_audit import (
    MAMOAuditError,
    prepare_mamo_replication,
    scan_opened_mamo_rows,
    select_mamo_adjudication,
)
from or_ci.nl4opt_audit import compare_model_run, read_jsonl


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _mamo_row(index: int, answer: object) -> dict:
    return {"en_question": f"Question {index}", "en_answer": answer}


def test_mamo_answer_policy_handles_status_markers_and_tolerance() -> None:
    assert answer_relation(
        -9999,
        "No Feasible Solution",
        policy=MAMO_EASYLP_ANSWER_POLICY,
    ) == "encoding_equivalent"
    assert answers_equal(10, 10.004, policy=MAMO_EASYLP_ANSWER_POLICY)
    assert not answers_equal(10, 10.006, policy=MAMO_EASYLP_ANSWER_POLICY)


def test_scan_opened_mamo_rows_records_prior_nested_session(tmp_path: Path) -> None:
    original = tmp_path / "MAMO_EasyLP.json"
    _write_jsonl(original, [_mamo_row(index, index) for index in range(3)])
    events = (
        tmp_path
        / "experiments"
        / "MAMO_EASYLP-0001"
        / "terra"
        / "codex-events.jsonl"
    )
    _write_jsonl(events, [{"type": "session.started"}])
    output = tmp_path / "opened.jsonl"

    summary = scan_opened_mamo_rows(
        experiments_root=tmp_path / "experiments",
        original_path=original,
        output_path=output,
    )

    rows = read_jsonl(output)
    assert summary["opened_rows"] == 1
    assert rows[0]["row_id"] == "mamo-easylp-row-0001"
    assert rows[0]["event_file_count"] == 1


def test_prepare_mamo_freezes_untouched_corrections_and_controls(tmp_path: Path) -> None:
    original_rows = [_mamo_row(index, index * 10) for index in range(8)]
    revised_rows = []
    for index, row in enumerate(original_rows):
        if index == 1:
            continue
        revised = dict(row)
        if index in {2, 3}:
            revised["en_answer"] = row["en_answer"] + 1
        revised_rows.append(revised)
    revised_rows.reverse()
    original = tmp_path / "original.jsonl"
    revised = tmp_path / "revised.jsonl"
    corrections = tmp_path / "corrections.json"
    opened = tmp_path / "opened.jsonl"
    output = tmp_path / "campaign"
    _write_jsonl(original, original_rows)
    _write_jsonl(revised, revised_rows)
    _write_json(
        corrections,
        {
            "index_base": 0,
            "removed_indices": [1],
            "question_revision_indices": [],
            "answer_correction_indices": [2, 3],
        },
    )
    _write_jsonl(opened, [{"dataset_index_zero": 3}])

    provenance = prepare_mamo_replication(
        original_path=original,
        revised_path=revised,
        correction_manifest_path=corrections,
        opened_manifest_path=opened,
        output_dir=output,
        original_commit="original-commit",
        revised_commit="revised-commit",
        seed="test-seed",
        corrected_count=1,
        control_count=2,
        min_revised_recovery=1,
        min_revision_discrimination=1,
        max_control_disagreement=1,
    )

    hidden = read_jsonl(output / "hidden" / "answer-key.jsonl")
    assert provenance["status"] == "frozen"
    assert provenance["counts"]["eligible_corrected_candidates"] == 1
    assert {row["selection_group"] for row in hidden} == {
        "answer_changed",
        "unchanged_control",
    }
    assert len(hidden) == 3
    assert provenance["schema_version"] == "mamo_benchmark_integrity_provenance_v2"
    assert provenance["evaluation_contract"]["required_terra_rows"] == 3
    assert (output / "source" / "canary-source-manifest.jsonl").is_file()


def test_prepare_mamo_writes_shortfall_evidence_before_failing(tmp_path: Path) -> None:
    original_rows = [_mamo_row(index, index) for index in range(4)]
    revised_rows = [dict(row) for row in original_rows]
    revised_rows[1]["en_question"] = "Unexpected question rewrite"
    revised_rows[1]["en_answer"] = 99
    original = tmp_path / "original.jsonl"
    revised = tmp_path / "revised.jsonl"
    corrections = tmp_path / "corrections.json"
    opened = tmp_path / "opened.jsonl"
    output = tmp_path / "campaign"
    _write_jsonl(original, original_rows)
    _write_jsonl(revised, revised_rows)
    _write_json(
        corrections,
        {
            "index_base": 0,
            "removed_indices": [],
            "question_revision_indices": [],
            "answer_correction_indices": [1],
        },
    )
    _write_jsonl(opened, [])

    with pytest.raises(MAMOAuditError, match="candidate shortfall"):
        prepare_mamo_replication(
            original_path=original,
            revised_path=revised,
            correction_manifest_path=corrections,
            opened_manifest_path=opened,
            output_dir=output,
            original_commit="original-commit",
            revised_commit="revised-commit",
            seed="test-seed",
            corrected_count=1,
            control_count=1,
            min_revised_recovery=1,
            min_revision_discrimination=1,
            max_control_disagreement=1,
        )

    provenance = json.loads(
        (output / "provenance" / "provenance.json").read_text(encoding="utf-8")
    )
    mapping = read_jsonl(output / "provenance" / "row-mapping-and-exclusions.jsonl")
    assert provenance["status"] == "blocked_candidate_shortfall"
    assert provenance["counts"]["eligible_corrected_candidates"] == 0
    assert mapping[1]["exclusion_reason"] == "undeclared_question_drift"
    assert not (output / "hidden" / "answer-key.jsonl").exists()


def test_prepare_mamo_rejects_gate_larger_than_denominator(tmp_path: Path) -> None:
    with pytest.raises(MAMOAuditError, match="minimum revised recovery exceeds"):
        prepare_mamo_replication(
            original_path=tmp_path / "original.jsonl",
            revised_path=tmp_path / "revised.jsonl",
            correction_manifest_path=tmp_path / "corrections.json",
            opened_manifest_path=tmp_path / "opened.jsonl",
            output_dir=tmp_path / "campaign",
            original_commit="original-commit",
            revised_commit="revised-commit",
            seed="test-seed",
            corrected_count=17,
            control_count=20,
            min_revised_recovery=18,
            min_revision_discrimination=11,
            max_control_disagreement=3,
        )


def _write_model_row(
    run_dir: Path,
    row_id: str,
    *,
    chosen_domain: str,
    continuous: dict,
    integer: dict,
) -> None:
    workspace = run_dir / "rows" / row_id
    _write_json(workspace / "run-manifest.json", {"terminal_status": "success"})
    _write_json(
        workspace / "audit.json",
        {
            "chosen_domain": chosen_domain,
            "source_status": "well_posed",
            "mechanisms": [],
            "material_ambiguities": [],
        },
    )
    _write_json(
        workspace / "parent_solver_report.json",
        {"continuous": continuous, "integer": integer},
    )


def test_compare_model_run_uses_selected_domain_and_fails_ambiguous_controls(
    tmp_path: Path,
) -> None:
    campaign = tmp_path / "campaign"
    run_dir = campaign / "runs" / "terra-evidence"
    corrected_id = "mamo-easylp-row-0002"
    control_id = "mamo-easylp-row-0004"
    _write_json(
        campaign / "provenance" / "provenance.json",
        {"corpus": "MAMO_EasyLP", "answer_policy": MAMO_EASYLP_ANSWER_POLICY.to_dict()},
    )
    _write_jsonl(
        campaign / "hidden" / "answer-key.jsonl",
        [
            {
                "row_id": corrected_id,
                "selection_group": "answer_changed",
                "historical_answer": 10,
                "corrected_answer": 12,
            },
            {
                "row_id": control_id,
                "selection_group": "unchanged_control",
                "historical_answer": 20,
                "corrected_answer": 20,
            },
        ],
    )
    manifest = [{"row_id": corrected_id}, {"row_id": control_id}]
    _write_jsonl(campaign / "source" / "evidence-source-manifest.jsonl", manifest)
    _write_jsonl(
        campaign / "source" / "sol-source-manifest.jsonl",
        [{"row_id": corrected_id}],
    )
    _write_model_row(
        run_dir,
        corrected_id,
        chosen_domain="integer",
        continuous={"status": "optimal", "objective": 10},
        integer={"status": 2, "objective": 12},
    )
    _write_model_row(
        run_dir,
        control_id,
        chosen_domain="both",
        continuous={"status": "optimal", "objective": 20},
        integer={"status": "optimal", "objective": 21},
    )

    rows = {
        row["row_id"]: row
        for row in compare_model_run(campaign_dir=campaign, run_dir=run_dir, role="terra")
    }

    assert rows[corrected_id]["revised_reproduced_selected_domain"] is True
    assert rows[corrected_id]["revised_discriminated_selected_domain"] is True
    assert rows[corrected_id]["domain_ambiguous"] is False
    assert rows[control_id]["domain_ambiguous"] is True
    assert rows[control_id]["unchanged_control_disagreement_selected_domain"] is True
    assert rows[corrected_id]["formal_target_recovers_correction"] is None

    sol_rows = compare_model_run(campaign_dir=campaign, run_dir=run_dir, role="sol")
    assert [row["row_id"] for row in sol_rows] == [corrected_id]


def test_select_mamo_adjudication_freezes_balanced_8_plus_4(tmp_path: Path) -> None:
    campaign = tmp_path / "campaign"
    rows: list[dict] = []
    source: list[dict] = []
    for index in range(20):
        row_id = f"mamo-easylp-row-{index:04d}"
        rows.append(
            {
                "row_id": row_id,
                "selection_group": "answer_changed",
                "terminal_status": "success",
                "revised_reproduced_selected_domain": index < 15,
                "revised_discriminated_selected_domain": index < 12,
                "domain_ambiguous": index >= 18,
                "chosen_domain": "unresolved" if index >= 18 else "integer",
            }
        )
        source.append({"row_id": row_id, "split": "mamo_replication_evidence"})
    for index in range(20, 40):
        row_id = f"mamo-easylp-row-{index:04d}"
        rows.append(
            {
                "row_id": row_id,
                "selection_group": "unchanged_control",
                "terminal_status": "success",
                "unchanged_control_disagreement_selected_domain": index < 23,
            }
        )
        source.append({"row_id": row_id, "split": "mamo_replication_evidence"})
    comparison = campaign / "comparisons" / "terra-answer-comparison.jsonl"
    _write_jsonl(comparison, rows)
    _write_jsonl(campaign / "source" / "evidence-source-manifest.jsonl", source)

    result = select_mamo_adjudication(
        campaign_dir=campaign,
        terra_comparison_path=comparison,
        seed="test-selection",
    )

    selected = read_jsonl(campaign / "source" / "sol-source-manifest.jsonl")
    selected_ids = {row["row_id"] for row in selected}
    assert result["status"] == "frozen"
    assert len(selected) == 12
    assert sum(int(row_id.rsplit("-", 1)[1]) >= 20 for row_id in selected_ids) == 4
    assert any(int(row_id.rsplit("-", 1)[1]) >= 23 for row_id in selected_ids)


def test_select_mamo_adjudication_uses_frozen_17_plus_20_gates(tmp_path: Path) -> None:
    contract = {
        "corrected_rows": 17,
        "control_rows": 20,
        "required_terra_rows": 37,
        "min_revised_recovery": 13,
        "min_revision_discrimination": 11,
        "max_control_disagreement": 3,
    }
    rows: list[dict] = []
    source: list[dict] = []
    for index in range(17):
        row_id = f"mamo-easylp-row-{index:04d}"
        rows.append(
            {
                "row_id": row_id,
                "selection_group": "answer_changed",
                "terminal_status": "success",
                "revised_reproduced_selected_domain": index < 13,
                "revised_discriminated_selected_domain": index < 11,
                "domain_ambiguous": index >= 15,
                "chosen_domain": "unresolved" if index >= 15 else "integer",
            }
        )
        source.append({"row_id": row_id, "split": "mamo_replication_evidence"})
    for index in range(17, 37):
        row_id = f"mamo-easylp-row-{index:04d}"
        rows.append(
            {
                "row_id": row_id,
                "selection_group": "unchanged_control",
                "terminal_status": "success",
                "unchanged_control_disagreement_selected_domain": index < 20,
            }
        )
        source.append({"row_id": row_id, "split": "mamo_replication_evidence"})

    campaign = tmp_path / "passing"
    comparison = campaign / "comparisons" / "terra-answer-comparison.jsonl"
    _write_json(
        campaign / "provenance" / "provenance.json",
        {"schema_version": "mamo_benchmark_integrity_provenance_v2", "evaluation_contract": contract},
    )
    _write_jsonl(comparison, rows)
    _write_jsonl(campaign / "source" / "evidence-source-manifest.jsonl", source)

    result = select_mamo_adjudication(
        campaign_dir=campaign,
        terra_comparison_path=comparison,
        seed="test-17-plus-20",
    )

    assert result["status"] == "frozen"
    assert result["gates"]["valid_terra_rows"]["required"] == 37
    assert result["gates"]["revised_recovery"]["required_minimum"] == 13
    assert result["gates"]["revision_discrimination"]["required_minimum"] == 11
    assert len(read_jsonl(campaign / "source" / "sol-source-manifest.jsonl")) == 12

    blocked_campaign = tmp_path / "blocked"
    blocked_rows = [dict(row) for row in rows]
    blocked_rows[12]["revised_reproduced_selected_domain"] = False
    blocked_comparison = blocked_campaign / "comparisons" / "terra-answer-comparison.jsonl"
    _write_json(
        blocked_campaign / "provenance" / "provenance.json",
        {"schema_version": "mamo_benchmark_integrity_provenance_v2", "evaluation_contract": contract},
    )
    _write_jsonl(blocked_comparison, blocked_rows)
    _write_jsonl(blocked_campaign / "source" / "evidence-source-manifest.jsonl", source)

    blocked = select_mamo_adjudication(
        campaign_dir=blocked_campaign,
        terra_comparison_path=blocked_comparison,
        seed="test-17-plus-20",
    )

    assert blocked["status"] == "blocked_terra_gate"
    assert blocked["gates"]["revised_recovery"]["pass"] is False
    assert not (blocked_campaign / "source" / "sol-source-manifest.jsonl").exists()
