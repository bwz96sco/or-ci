from __future__ import annotations

import csv
import json
from pathlib import Path

from or_ci.nl4opt_audit import sha256_file, sha256_text
from or_ci.nl4opt_census import (
    FIXED_SOL_CONTROL_IDS,
    _terra_sol_agree,
    classify_census_rows,
    finalize_nl4opt_census,
    merge_nl4opt_census_terra,
    reconcile_nl4opt_evidence,
    select_census_controls,
    select_nl4opt_census_adjudication,
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_classification_and_control_ranking_are_deterministic() -> None:
    historical = [
        {"en_question": "A", "en_answer": "1"},
        {"en_question": "B", "en_answer": "2"},
    ]
    corrected = [
        {"en_question": "A", "en_answer": "1"},
        {"en_question": "B", "en_answer": "3"},
    ]
    mappings = [
        {"row_id": "nl4opt-row-0001", "source_id": "a"},
        {"row_id": "nl4opt-row-0002", "source_id": "b"},
    ]
    solver = [
        {
            "source_id": "a",
            "continuous": {"status": "optimal", "objective": 1.0},
            "integer": {"status": "optimal", "objective": 1.0},
        },
        {
            "source_id": "b",
            "continuous": {"status": "optimal", "objective": 3.0},
            "integer": {"status": "optimal", "objective": 3.0},
        },
    ]

    _, rows = classify_census_rows(
        historical_rows=historical,
        corrected_rows=corrected,
        mappings=mappings,
        solver_rows=solver,
    )

    assert rows[0]["target_match"] == "match_both"
    assert rows[1]["target_match"] == "match_corrected_only"
    controls = select_census_controls(
        [
            {
                **rows[0],
                "row_id": f"nl4opt-row-{index:04d}",
                "domain_stability": domain,
            }
            for index, domain in ((1, "stable"), (2, "stable"), (3, "ambiguous"), (4, "ambiguous"))
        ],
        seed="fixture",
        excluded_row_ids=set(),
        per_domain_class=1,
    )
    assert controls == select_census_controls(
        [
            {
                **rows[0],
                "row_id": f"nl4opt-row-{index:04d}",
                "domain_stability": domain,
            }
            for index, domain in ((1, "stable"), (2, "stable"), (3, "ambiguous"), (4, "ambiguous"))
        ],
        seed="fixture",
        excluded_row_ids=set(),
        per_domain_class=1,
    )


def test_solver_agreement_canonicalizes_unattained_supremum_aliases() -> None:
    terra = {
        "continuous_status": "UNATTAINED_SUPREMUM_STRICT_INEQUALITY",
        "continuous_objective": None,
        "integer_status": "OPTIMAL",
        "integer_objective": 76.0,
    }
    sol = {
        "continuous_status": "SUPREMUM_NOT_ATTAINED",
        "continuous_objective": 85.71428571428572,
        "integer_status": "OPTIMAL",
        "integer_objective": 76.0,
    }

    assert _terra_sol_agree(terra, sol) is True


def test_reconcile_evidence_tracks_states_and_keeps_row0072_invalid(tmp_path: Path) -> None:
    campaign = tmp_path / "campaign"
    july = tmp_path / "july"
    june = tmp_path / "june"
    row_specs = [
        ("nl4opt-row-0001", 1, "Question one"),
        ("nl4opt-row-0002", 2, "Question two"),
        ("nl4opt-row-0072", 72, "Question seventy two"),
    ]
    census_rows: list[dict] = []
    source_rows: list[dict] = []
    for row_id, number, question in row_specs:
        statement = campaign / "source" / "statements" / f"{row_id}.txt"
        statement.parent.mkdir(parents=True, exist_ok=True)
        statement.write_text(question + "\n", encoding="utf-8")
        source_rows.append(
            {
                "row_id": row_id,
                "split": "census",
                "statement_path": f"source/statements/{row_id}.txt",
                "source_sha256": sha256_file(statement),
            }
        )
        census_rows.append(
            {
                "row_id": row_id,
                "dataset_row_number": number,
                "dataset_question_sha256": sha256_text(question),
                "candidate": row_id == "nl4opt-row-0072",
            }
        )
    _write_jsonl(campaign / "census" / "census-rows.jsonl", census_rows)
    _write_jsonl(campaign / "source" / "census-source-manifest.jsonl", source_rows)
    _write_csv(
        june / "stage1_generation_manifest.csv",
        [
            {
                "case_id": f"NL4OPT-{number:04d}",
                "source_row_index": number,
                "question_sha256": sha256_text(question),
            }
            for _, number, question in row_specs[:2]
        ],
        ["case_id", "source_row_index", "question_sha256"],
    )
    july_source: list[dict] = []
    batch: list[dict] = []
    revalidation: list[dict] = []
    comparison: list[dict] = []
    for row_id, _, question in row_specs[1:]:
        statement = july / "source" / "statements" / f"{row_id}.txt"
        statement.parent.mkdir(parents=True, exist_ok=True)
        statement.write_text(question + "\n", encoding="utf-8")
        source_hash = sha256_file(statement)
        july_source.append(
            {
                "row_id": row_id,
                "split": "pilot_evidence",
                "statement_path": f"source/statements/{row_id}.txt",
                "source_sha256": source_hash,
            }
        )
        batch.append(
            {
                "row_id": row_id,
                "terminal_status": "success",
                "source_sha256": source_hash,
                "model": "gpt-5.6-terra",
                "reasoning_effort": "high",
            }
        )
        revalidation.append(
            {
                "row_id": row_id,
                "effective_terminal_status": "success",
                "validation": {"status": "valid"},
            }
        )
        comparison.append({"row_id": row_id, "terminal_status": "success"})
        workspace = july / "runs" / "terra-evidence" / "rows" / row_id
        for name in ("run-manifest.json", "problem.json", "audit.json", "parent_solver_report.json"):
            _write_json(workspace / name, {})
    _write_jsonl(july / "source" / "evidence-source-manifest.jsonl", july_source)
    _write_jsonl(july / "runs" / "terra-evidence" / "batch-results.jsonl", batch)
    _write_json(
        july / "runs" / "terra-evidence" / "revalidation-summary.json",
        {"results": revalidation},
    )
    _write_jsonl(july / "comparisons" / "terra-answer-comparison.jsonl", comparison)

    summary = reconcile_nl4opt_evidence(
        campaign_dir=campaign,
        june_manifest_dir=june,
        july_pilot_campaign_dir=july,
        enforce_approved_counts=False,
    )

    assert summary["evidence_state_counts"] == {
        "june_only": 1,
        "june_plus_july": 1,
        "july_only": 1,
    }
    ledger = {
        row["row_id"]: row
        for row in json.loads("[" + ",".join(
            (campaign / "provenance" / "evidence-reconciliation.jsonl").read_text().splitlines()
        ) + "]")
    }
    assert ledger["nl4opt-row-0072"]["july_modern_valid"] is False


def test_merge_builds_26_plus_10_and_preserves_delta(tmp_path: Path) -> None:
    campaign = tmp_path / "campaign"
    july = tmp_path / "july"
    candidate_ids = [f"nl4opt-row-{index:04d}" for index in range(1, 27)]
    delta_ids = candidate_ids[:12]
    reuse_ids = candidate_ids[12:]
    control_ids = [f"nl4opt-row-{index:04d}" for index in range(101, 111)]
    _write_json(
        campaign / "provenance" / "census-selection.json",
        {
            "valid_modern_july_candidate_reuse_ids": reuse_ids,
            "terra_candidate_delta_ids": delta_ids,
            "stable_control_ids": control_ids[:5],
            "ambiguous_control_ids": control_ids[5:],
        },
    )
    census = [
        {
            "row_id": row_id,
            "census_group": "candidate" if row_id in candidate_ids else "control",
            "target_match": "match_neither" if row_id in candidate_ids else "match_both",
            "domain_ambiguous": False,
        }
        for row_id in [*candidate_ids, *control_ids]
    ]
    official = [
        {
            "row_id": row["row_id"],
            "continuous": {"status": "optimal", "objective": 1.0},
            "integer": {"status": "optimal", "objective": 1.0},
        }
        for row in census
    ]
    comparison = lambda row_id: {
        "row_id": row_id,
        "terminal_status": "success",
        "chosen_domain": "both",
        "continuous_status": "optimal",
        "continuous_objective": 1.0,
        "integer_status": "optimal",
        "integer_objective": 1.0,
    }
    _write_jsonl(campaign / "census" / "census-rows.jsonl", census)
    _write_jsonl(
        campaign / "deterministic" / "mapped-official-solver-results.jsonl", official
    )
    delta_path = campaign / "comparisons" / "incoming-delta.jsonl"
    _write_jsonl(delta_path, [comparison(row_id) for row_id in [*delta_ids, *control_ids]])
    (july / "source").mkdir(parents=True)
    _write_jsonl(
        july / "comparisons" / "terra-answer-comparison.jsonl",
        [comparison(row_id) for row_id in reuse_ids],
    )

    summary = merge_nl4opt_census_terra(
        campaign_dir=campaign,
        july_pilot_campaign_dir=july,
        delta_comparison_path=delta_path,
    )

    assert summary["rows"] == 36
    assert summary["candidates"] == 26
    assert summary["controls"] == 10
    assert len((campaign / "comparisons" / "terra-delta-answer-comparison.jsonl").read_text().splitlines()) == 22


def test_sol_selection_is_deterministic_and_answer_blind(tmp_path: Path) -> None:
    campaign = tmp_path / "campaign"
    candidate_ids = [f"nl4opt-row-{index:04d}" for index in range(1, 11)]
    all_ids = [*candidate_ids, *FIXED_SOL_CONTROL_IDS]
    terra: list[dict] = []
    for index, row_id in enumerate(candidate_ids):
        terra.append(
            {
                "row_id": row_id,
                "census_group": "candidate",
                "terminal_status": "success",
                "terra_valid": True,
                "interface_class": "source_target_conflict",
                "source_target_conflict": True,
                "solver_status_conflict": index % 2 == 0,
                "numeric_answer_conflict": index % 3 == 0,
                "domain_ambiguity": index % 4 == 0,
                "answer_relation": (
                    "encoding_equivalent" if row_id == candidate_ids[1] else "semantic_difference"
                ),
            }
        )
    terra.extend(
        {
            "row_id": row_id,
            "census_group": "control",
            "terminal_status": "success",
            "terra_valid": True,
            "interface_class": "source_target_agreement",
        }
        for row_id in FIXED_SOL_CONTROL_IDS
    )
    _write_jsonl(campaign / "comparisons" / "terra-answer-comparison.jsonl", terra)
    _write_jsonl(
        campaign / "source" / "census-source-manifest.jsonl",
        [
            {
                "row_id": row_id,
                "split": "census",
                "statement_path": f"source/statements/{row_id}.txt",
                "source_sha256": sha256_text(row_id),
            }
            for row_id in all_ids
        ],
    )
    prior = tmp_path / "prior.csv"
    _write_csv(prior, [{"row_id": candidate_ids[0]}], ["row_id"])

    first = select_nl4opt_census_adjudication(
        campaign_dir=campaign,
        prior_owner_packet_path=prior,
        seed="fixture",
        enforce_campaign_gates=False,
    )
    second = select_nl4opt_census_adjudication(
        campaign_dir=campaign,
        prior_owner_packet_path=prior,
        seed="fixture",
        enforce_campaign_gates=False,
    )

    assert first["selected_candidate_row_ids"] == second["selected_candidate_row_ids"]
    assert candidate_ids[0] not in first["selected_candidate_row_ids"]
    assert candidate_ids[1] not in first["selected_candidate_row_ids"]
    assert len(first["selected_candidate_row_ids"]) == 8
    manifest = [json.loads(line) for line in (campaign / "source" / "sol-source-manifest.jsonl").read_text().splitlines()]
    assert all(set(row) == {"row_id", "split", "statement_path", "source_sha256"} for row in manifest)
    assert "answer" not in (campaign / "source" / "sol-source-manifest.jsonl").read_text().lower()


def test_finalizer_pass_pending_and_failed_routes(tmp_path: Path) -> None:
    campaign = tmp_path / "campaign"
    candidate_ids = [f"nl4opt-row-{index:04d}" for index in range(301, 327)]
    control_ids = [
        "nl4opt-row-0068",
        "nl4opt-row-0061",
        "nl4opt-row-0010",
        "nl4opt-row-0192",
        "nl4opt-row-0065",
        "nl4opt-row-0055",
        "nl4opt-row-0207",
        "nl4opt-row-0026",
        "nl4opt-row-0245",
        "nl4opt-row-0184",
    ]
    sol_ids = [*candidate_ids[:8], *FIXED_SOL_CONTROL_IDS]
    all_ids = [*candidate_ids, *control_ids]
    census = [
        {
            "row_id": row_id,
            "candidate": row_id in candidate_ids,
            "census_group": "candidate" if row_id in candidate_ids else "control",
            "target_match": "match_neither" if row_id in candidate_ids else "match_both",
        }
        for row_id in all_ids
    ]
    terra_comparison = [
        {
            "row_id": row_id,
            "terminal_status": "success",
            "terra_valid": True,
            "chosen_domain": "both",
            "continuous_status": "optimal",
            "continuous_objective": 1.0,
            "integer_status": "optimal",
            "integer_objective": 1.0,
            "source_target_conflict": row_id in candidate_ids[:3],
        }
        for row_id in all_ids
    ]
    sol_comparison = [
        {key: value for key, value in row.items() if key != "terra_valid"}
        for row in terra_comparison
        if row["row_id"] in sol_ids
    ]
    sol_comparison[0]["chosen_domain"] = "integer"
    _write_jsonl(campaign / "census" / "census-rows.jsonl", census)
    _write_jsonl(
        campaign / "comparisons" / "terra-answer-comparison.jsonl", terra_comparison
    )
    _write_jsonl(
        campaign / "comparisons" / "sol-answer-comparison.jsonl", sol_comparison
    )
    _write_jsonl(
        campaign / "source" / "sol-source-manifest.jsonl",
        [{"row_id": row_id} for row_id in sol_ids],
    )
    _write_json(
        campaign / "provenance" / "census-selection.json",
        {
            "terra_candidate_delta_ids": candidate_ids[:12],
            "stable_control_ids": control_ids[:5],
            "ambiguous_control_ids": control_ids[5:],
        },
    )
    _write_json(
        campaign / "provenance" / "sol-selection.json",
        {"prior_owner_packet_row_ids": []},
    )
    decisions = ["dataset_supported", "both_valid", "sirl_supported"]
    mechanisms = [
        "reference_value_or_arithmetic_error",
        "domain_or_integrality_ambiguity",
        "constraint_or_ratio_interpretation",
    ]
    owner_rows = []
    for row_id in sol_ids:
        action_index = candidate_ids[:3].index(row_id) if row_id in candidate_ids[:3] else None
        owner_rows.append(
            {
                "row_id": row_id,
                "owner_decision": decisions[action_index] if action_index is not None else "dataset_supported",
                "owner_material": "yes" if action_index is not None else "no",
                "owner_mechanism": mechanisms[action_index] if action_index is not None else "none",
                "model_agreement": "True",
            }
        )
    owner_fields = list(owner_rows[0])
    _write_csv(campaign / "owner-review" / "owner-review-packet.csv", owner_rows, owner_fields)
    _write_json(
        campaign / "owner-review" / "owner-review-status.json",
        {"status": "valid_complete"},
    )
    _write_json(
        campaign / "provenance" / "evidence-source-manifest-validation.json",
        {"status": "valid"},
    )
    _write_json(
        campaign / "provenance" / "sol-source-manifest-validation.json",
        {"status": "valid"},
    )
    _write_json(
        campaign / "runs" / "terra-evidence" / "batch-summary.json",
        {"sessions_started": 22, "terminal_counts": {"success": 22, "leakage_blocked": 0}},
    )
    _write_json(
        campaign / "runs" / "sol-adjudication" / "batch-summary.json",
        {"sessions_started": 12, "terminal_counts": {"success": 12, "leakage_blocked": 0}},
    )

    passed = finalize_nl4opt_census(campaign_dir=campaign)
    assert passed["next_route"] == "evaluation_impact_campaign"
    assert passed["paper_writing_allowed"] is False
    agreement_rows = {
        row["row_id"]: row
        for row in (
            json.loads(line)
            for line in (
                campaign / "comparisons" / "terra-sol-agreement.jsonl"
            ).read_text().splitlines()
        )
    }
    assert agreement_rows[sol_ids[0]]["domain_assessment_agreement"] is False
    assert agreement_rows[sol_ids[0]]["solver_result_agreement"] is True

    _write_json(campaign / "owner-review" / "owner-review-status.json", {"status": "pending"})
    pending = finalize_nl4opt_census(campaign_dir=campaign)
    assert pending["next_route"] == "blocked_owner_review"

    for row in sol_comparison[:3]:
        row["continuous_objective"] = 2.0
    _write_jsonl(
        campaign / "comparisons" / "sol-answer-comparison.jsonl", sol_comparison
    )
    machine_failed = finalize_nl4opt_census(campaign_dir=campaign)
    assert machine_failed["machine_gate_pass"] is False
    assert machine_failed["next_route"] == "park_stop_scaling"
    assert machine_failed["owner_review_required"] is False
    assert machine_failed["owner_status"] == "skipped_pre_owner_machine_gate_failure"
    assert machine_failed["owner_source_status"] == "pending"

    for row in sol_comparison[:3]:
        row["continuous_objective"] = 1.0
    _write_jsonl(
        campaign / "comparisons" / "sol-answer-comparison.jsonl", sol_comparison
    )

    owner_rows[0]["owner_material"] = "no"
    _write_csv(campaign / "owner-review" / "owner-review-packet.csv", owner_rows, owner_fields)
    _write_json(
        campaign / "owner-review" / "owner-review-status.json",
        {"status": "valid_complete"},
    )
    failed = finalize_nl4opt_census(campaign_dir=campaign)
    assert failed["next_route"] == "park_stop_scaling"
