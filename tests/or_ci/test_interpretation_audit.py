from __future__ import annotations

import json
from pathlib import Path

import pytest

from or_ci.interpretation_audit import (
    InterpretationAuditError,
    compare_industryor_runs,
    evaluate_interpretation_run,
    finalize_industryor_interpretation,
    prepare_industryor_interpretation,
    scan_opened_industryor_rows,
    select_interpretation_adjudication,
)
from or_ci.nl4opt_audit import read_jsonl


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _industry_row(index: int, difficulty: str) -> dict:
    return {
        "id": index,
        "difficulty": difficulty,
        "en_question": f"Maximize output for factory {index}.",
        "en_answer": float(index),
    }


def test_scan_and_prepare_industryor_stratifies_without_answer_leakage(tmp_path: Path) -> None:
    dataset = tmp_path / "industryor.jsonl"
    rows = [
        _industry_row(offset + index, difficulty)
        for difficulty, offset in (("Easy", 0), ("Medium", 100), ("Hard", 200))
        for index in range(1, 5)
    ]
    _write_jsonl(dataset, rows)
    events = tmp_path / "experiments" / "INDUSTRYOR-1" / "terra" / "codex-events.jsonl"
    _write_jsonl(events, [{"type": "session.started"}])
    opened = tmp_path / "opened.jsonl"

    scan = scan_opened_industryor_rows(
        experiments_root=tmp_path / "experiments",
        dataset_path=dataset,
        output_path=opened,
    )
    prepared = prepare_industryor_interpretation(
        dataset_path=dataset,
        opened_manifest_path=opened,
        output_dir=tmp_path / "campaign",
        dataset_commit="fixture-commit",
        seed="fixture-seed",
        per_difficulty=2,
    )

    source = read_jsonl(tmp_path / "campaign" / "source" / "evidence-source-manifest.jsonl")
    hidden = read_jsonl(tmp_path / "campaign" / "hidden" / "answer-key.jsonl")
    assert scan["opened_rows"] == 1
    assert prepared["selected"] == 6
    assert {row["split"] for row in source} == {
        "industryor_easy",
        "industryor_medium",
        "industryor_hard",
    }
    assert all("answer" not in json.dumps(row).lower() for row in source)
    assert all("reference_answer" in row for row in hidden)
    assert "industryor-row-0001" not in {row["row_id"] for row in source}


def test_development_gate_enforces_valid_material_and_leakage_thresholds(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    for index in range(7):
        row_id = f"row-{index}"
        workspace = run_dir / "rows" / row_id
        _write_json(
            workspace / "run-manifest.json",
            {
                "terminal_status": "success" if index < 6 else "artifact_invalid",
                "leakage_findings": [],
            },
        )
        if index < 6:
            _write_json(
                workspace / "validated-interpretation-set.json",
                {"material_multi_variant": index < 5},
            )

    result = evaluate_interpretation_run(
        run_dir=run_dir,
        output_path=tmp_path / "development-gate.json",
        expected_rows=7,
        min_valid=6,
        min_material_multi_variant=5,
    )

    assert result["status"] == "pass"
    assert result["authorized_next_wave"] is True
    assert result["valid_rows"] == 6
    assert result["material_multi_variant_rows"] == 5


def _solver_result(objective: float) -> dict:
    return {"status": "optimal", "objective": objective}


def _write_baseline_row(run_dir: Path, row_id: str, answer: float) -> None:
    workspace = run_dir / "rows" / row_id
    _write_json(workspace / "run-manifest.json", {"terminal_status": "success", "leakage_findings": []})
    _write_json(
        workspace / "audit.json",
        {"chosen_domain": "continuous", "source_status": "well_posed"},
    )
    _write_json(
        workspace / "parent_solver_report.json",
        {"continuous": _solver_result(answer), "integer": _solver_result(answer)},
    )


def _write_candidate_row(
    run_dir: Path,
    row_id: str,
    answer: float,
    *,
    material: bool,
    partial: bool,
) -> None:
    workspace = run_dir / "rows" / row_id
    _write_json(workspace / "run-manifest.json", {"terminal_status": "success", "leakage_findings": []})
    objectives = [answer, answer + 10.0] if partial else [answer, answer]
    variants = []
    for index, objective in enumerate(objectives, start=1):
        variant_id = f"v{index}"
        domain = "continuous" if index == 1 else "integer"
        fingerprint = f"fingerprint-{row_id}-{index if material else 1}"
        variants.append(
            {
                "variant_id": variant_id,
                "domain": domain,
                "changed_assumption": "variables may be fractional" if index == 1 else "variables are integral",
                "material": material,
                "source_quotes": ["factory"],
                "model_ir_fingerprint": fingerprint,
                "selected_result": _solver_result(objective),
            }
        )
        variant_dir = workspace / "variants" / variant_id
        _write_json(
            variant_dir / "problem.json",
            {"sense": "maximize", "variables": [{"name": "x", "domain": domain}]},
        )
        _write_json(
            variant_dir / "parent_model_ir.json",
            {
                "continuous": {"sense": "maximize", "variables": [{"name": "x", "domain": "continuous"}]},
                "integer": {"sense": "maximize", "variables": [{"name": "x", "domain": "integer"}]},
            },
        )
    _write_json(
        workspace / "validated-interpretation-set.json",
        {
            "enumeration_status": "within_cap",
            "material_multi_variant": material,
            "variants": variants,
        },
    )


def _build_main_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    campaign = tmp_path / "campaign"
    baseline = tmp_path / "baseline"
    candidate = tmp_path / "candidate"
    source_rows = []
    hidden_rows = []
    for index in range(1, 25):
        row_id = f"industryor-row-{index:04d}"
        answer = float(index)
        statement = campaign / "source" / "statements" / f"INDUSTRYOR-{index}.txt"
        statement.parent.mkdir(parents=True, exist_ok=True)
        statement.write_text(f"Maximize factory {index}.\n", encoding="utf-8")
        source_rows.append(
            {
                "row_id": row_id,
                "split": "industryor_easy" if index <= 8 else "industryor_medium" if index <= 16 else "industryor_hard",
                "statement_path": str(statement.relative_to(campaign)),
                "source_sha256": f"sha-{index}",
            }
        )
        hidden_rows.append(
            {
                "row_id": row_id,
                "dataset_id": f"INDUSTRYOR-{index}",
                "dataset_numeric_id": index,
                "difficulty": "Easy" if index <= 8 else "Medium" if index <= 16 else "Hard",
                "reference_answer": answer,
            }
        )
        _write_baseline_row(baseline, row_id, answer)
        _write_candidate_row(
            candidate,
            row_id,
            answer,
            material=index <= 8,
            partial=index <= 8,
        )
    _write_jsonl(campaign / "source" / "evidence-source-manifest.jsonl", source_rows)
    _write_jsonl(campaign / "hidden" / "answer-key.jsonl", hidden_rows)
    return campaign, baseline, candidate


def test_main_comparison_selection_and_sol_gate_are_replayable(tmp_path: Path) -> None:
    campaign, baseline, candidate = _build_main_fixture(tmp_path)

    terra = compare_industryor_runs(
        campaign_dir=campaign,
        baseline_run_dir=baseline,
        candidate_run_dir=candidate,
    )
    selection = select_interpretation_adjudication(
        campaign_dir=campaign,
        candidate_run_dir=candidate,
        seed="sol-fixture",
    )

    assert terra["main_gate_pass"] is True
    assert terra["candidate_categories"]["partially_supported"] == 8
    assert terra["candidate_categories"]["robustly_supported"] == 16
    assert selection["selected_disputed"] == 8
    assert selection["selected_robust_controls"] == 4
    sol_manifest = read_jsonl(campaign / "source" / "sol-interpretation-manifest.jsonl")
    serialized_packets = "".join(
        (campaign / row["packet_path"]).read_text(encoding="utf-8") for row in sol_manifest
    ).lower()
    assert "reference_answer" not in serialized_packets
    assert '"answer"' not in serialized_packets

    sol_run = tmp_path / "sol"
    for row in sol_manifest:
        packet = json.loads((campaign / row["packet_path"]).read_text(encoding="utf-8"))
        workspace = sol_run / "rows" / row["row_id"]
        _write_json(workspace / "run-manifest.json", {"terminal_status": "success"})
        _write_json(
            workspace / "adjudication.json",
            {
                "obvious_omission": False,
                "variants": [
                    {
                        "variant_id": variant["variant_id"],
                        "support_status": "supported",
                        "material": variant["material"],
                    }
                    for variant in packet["variants"]
                ],
            },
        )

    final = finalize_industryor_interpretation(campaign_dir=campaign, sol_run_dir=sol_run)
    assert final["sol_valid_rows"] == 12
    assert final["category_agreement_rate"] == 1.0
    assert final["material_multi_variant_rows_after_sol"] == 8
    assert final["verdict"] == "continue_to_external_confirmatory_campaign"
    assert final["paper_writing_allowed"] is False


def test_sol_packet_rejects_hidden_answer_keys(tmp_path: Path) -> None:
    campaign, baseline, candidate = _build_main_fixture(tmp_path)
    compare_industryor_runs(
        campaign_dir=campaign,
        baseline_run_dir=baseline,
        candidate_run_dir=candidate,
    )
    first_problem = candidate / "rows" / "industryor-row-0001" / "variants" / "v1" / "problem.json"
    _write_json(first_problem, {"reference_answer": 1.0})

    with pytest.raises(InterpretationAuditError, match="forbidden keys"):
        select_interpretation_adjudication(
            campaign_dir=campaign,
            candidate_run_dir=candidate,
            seed="sol-fixture",
        )


def test_sol_selection_fills_low_signal_sample_without_changing_controls(tmp_path: Path) -> None:
    campaign, baseline, candidate = _build_main_fixture(tmp_path)
    for index in range(1, 9):
        row_id = f"industryor-row-{index:04d}"
        _write_candidate_row(candidate, row_id, float(index), material=False, partial=False)
    compare_industryor_runs(
        campaign_dir=campaign,
        baseline_run_dir=baseline,
        candidate_run_dir=candidate,
    )

    selection = select_interpretation_adjudication(
        campaign_dir=campaign,
        candidate_run_dir=candidate,
        seed="low-signal-fixture",
    )

    assert selection["selected_disputed"] == 0
    assert selection["selected_signal_screens"] == 8
    assert selection["selected_robust_controls"] == 4
    assert selection["selected_total"] == 12
