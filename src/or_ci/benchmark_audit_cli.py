from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from or_ci.interpretation_audit import (
    InterpretationAuditError,
    compare_industryor_runs,
    evaluate_interpretation_run,
    finalize_industryor_interpretation,
    prepare_industryor_interpretation,
    scan_opened_industryor_rows,
    select_interpretation_adjudication,
)
from or_ci.mamo_audit import (
    prepare_mamo_replication,
    scan_opened_mamo_rows,
    select_mamo_adjudication,
)
from or_ci.nl4opt_census import (
    finalize_nl4opt_census,
    merge_nl4opt_census_terra,
    prepare_nl4opt_census,
    reconcile_nl4opt_evidence,
    select_nl4opt_census_adjudication,
)
from or_ci.nl4opt_audit import (
    NL4OPTError,
    build_owner_review_packet,
    compare_formal_target_results,
    compare_model_run,
    load_official_targets,
    prepare_pilot,
    read_jsonl,
    solve_official_targets,
    solve_pilot_targets,
    validate_owner_review_packet,
    validate_source_manifest,
    write_json,
    write_jsonl,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare and evaluate answer-blind benchmark-integrity audits")
    subparsers = parser.add_subparsers(dest="command")

    prepare = subparsers.add_parser("prepare-nl4opt", help="freeze provenance, row mapping, and pilot rows")
    prepare.add_argument("--official", type=Path, required=True)
    prepare.add_argument("--historical", type=Path, required=True)
    prepare.add_argument("--corrected", type=Path, required=True)
    prepare.add_argument("--official-commit", required=True)
    prepare.add_argument("--corrected-commit", required=True)
    prepare.add_argument("--out-dir", type=Path, required=True)
    prepare.add_argument("--seed", default="nl4opt-benchmark-integrity-pilot-v1")
    prepare.add_argument("--control-count", type=int, default=16)
    prepare.add_argument("--expected-answer-changes", type=int, default=22)
    prepare.add_argument("--override-map", type=Path)

    prepare_census = subparsers.add_parser(
        "prepare-nl4opt-census",
        help="freeze the approved 245-row NL4OPT benchmark-integrity census",
    )
    prepare_census.add_argument("--official", type=Path, required=True)
    prepare_census.add_argument("--historical", type=Path, required=True)
    prepare_census.add_argument("--corrected", type=Path, required=True)
    prepare_census.add_argument(
        "--all-official-solver-results",
        "--all-official-results",
        dest="all_official_solver_results",
        type=Path,
        required=True,
    )
    prepare_census.add_argument(
        "--july-pilot-campaign-dir",
        "--july-pilot-dir",
        dest="july_pilot_campaign_dir",
        type=Path,
        required=True,
    )
    prepare_census.add_argument("--official-commit", required=True)
    prepare_census.add_argument("--corrected-commit", required=True)
    prepare_census.add_argument("--out-dir", type=Path, required=True)
    prepare_census.add_argument("--seed", default="nl4opt-full-census-v1")
    prepare_census.add_argument("--override-map", type=Path)

    reconcile_census = subparsers.add_parser(
        "reconcile-nl4opt-evidence",
        help="reconcile June candidate-only and validated July NL4OPT evidence",
    )
    reconcile_census.add_argument("--campaign-dir", type=Path, required=True)
    reconcile_census.add_argument(
        "--june-manifest-dir",
        "--june-dir",
        dest="june_manifest_dir",
        type=Path,
        required=True,
    )
    reconcile_census.add_argument(
        "--july-pilot-campaign-dir",
        "--july-pilot-dir",
        dest="july_pilot_campaign_dir",
        type=Path,
        required=True,
    )
    reconcile_census.add_argument("--out", type=Path)
    reconcile_census.add_argument("--summary-out", type=Path)

    merge_census = subparsers.add_parser(
        "merge-nl4opt-census-terra",
        help="merge valid July reuse with the census Terra delta and controls",
    )
    merge_census.add_argument("--campaign-dir", type=Path, required=True)
    merge_census.add_argument(
        "--july-pilot-campaign-dir",
        "--july-pilot-dir",
        dest="july_pilot_campaign_dir",
        type=Path,
        required=True,
    )
    merge_census.add_argument(
        "--terra-comparison", "--delta-comparison", dest="delta_comparison", type=Path
    )
    merge_census.add_argument("--terra-run-dir", "--delta-run-dir", dest="delta_run_dir", type=Path)
    merge_census.add_argument("--out", type=Path)

    select_census = subparsers.add_parser(
        "select-nl4opt-census-adjudication",
        help="freeze the prioritized answer-blind NL4OPT census Sol packet",
    )
    select_census.add_argument("--campaign-dir", type=Path, required=True)
    select_census.add_argument("--terra-comparison", type=Path)
    select_census.add_argument("--prior-owner-packet", type=Path)
    select_census.add_argument("--seed", default="nl4opt-full-census-sol-v1")
    select_census.add_argument("--max-candidates", type=int, default=8)

    finalize_census = subparsers.add_parser(
        "finalize-nl4opt-census",
        help="derive maintenance actions and the bounded NL4OPT census route",
    )
    finalize_census.add_argument("--campaign-dir", type=Path, required=True)
    finalize_census.add_argument("--terra-comparison", type=Path)
    finalize_census.add_argument("--sol-comparison", type=Path)
    finalize_census.add_argument("--owner-csv", type=Path)
    finalize_census.add_argument("--owner-status", type=Path)
    finalize_census.add_argument("--census-rows", type=Path)
    finalize_census.add_argument("--terra-run-summary", type=Path)
    finalize_census.add_argument("--sol-run-summary", type=Path)
    finalize_census.add_argument("--out", type=Path)

    scan_mamo = subparsers.add_parser(
        "scan-mamo-opened",
        help="freeze a conservative ledger of MAMO rows opened by prior nested Codex sessions",
    )
    scan_mamo.add_argument("--experiments-root", type=Path, required=True)
    scan_mamo.add_argument("--original", type=Path, required=True)
    scan_mamo.add_argument("--out", type=Path, required=True)

    prepare_mamo = subparsers.add_parser(
        "prepare-mamo",
        help="freeze untouched MAMO answer-correction and unchanged-control rows",
    )
    prepare_mamo.add_argument("--original", type=Path, required=True)
    prepare_mamo.add_argument("--revised", type=Path, required=True)
    prepare_mamo.add_argument("--correction-manifest", type=Path, required=True)
    prepare_mamo.add_argument("--opened-manifest", type=Path, required=True)
    prepare_mamo.add_argument("--original-commit", required=True)
    prepare_mamo.add_argument("--revised-commit", required=True)
    prepare_mamo.add_argument("--out-dir", type=Path, required=True)
    prepare_mamo.add_argument("--seed", default="mamo-easylp-2026-07")
    prepare_mamo.add_argument("--corrected-count", type=int, default=20)
    prepare_mamo.add_argument("--control-count", type=int, default=20)
    prepare_mamo.add_argument("--min-revised-recovery", type=int, default=15)
    prepare_mamo.add_argument("--min-revision-discrimination", type=int, default=12)
    prepare_mamo.add_argument("--max-control-disagreement", type=int, default=3)

    solve_all = subparsers.add_parser("solve-official", help="parse and solve every official structured target")
    solve_all.add_argument("--official", type=Path, required=True)
    solve_all.add_argument("--out", type=Path, required=True)

    solve_pilot = subparsers.add_parser("solve-pilot", help="solve frozen pilot formal targets")
    solve_pilot.add_argument("--campaign-dir", type=Path, required=True)

    compare = subparsers.add_parser("compare-formal", help="compare formal-target solves with hidden snapshots")
    compare.add_argument("--campaign-dir", type=Path, required=True)

    validate = subparsers.add_parser("validate-source-manifest", help="fail closed on answer leakage")
    validate.add_argument("--campaign-dir", type=Path, required=True)
    validate.add_argument("--manifest", type=Path, required=True)
    validate.add_argument("--out", type=Path)

    select = subparsers.add_parser("select-adjudication", help="freeze source-only Sol adjudication rows")
    select.add_argument("--campaign-dir", type=Path, required=True)
    select.add_argument("--terra-comparison", type=Path, required=True)
    select.add_argument("--seed", default="nl4opt-sol-adjudication-v1")
    select.add_argument("--discrepancies", type=int, default=8)
    select.add_argument("--clean-controls", type=int, default=4)

    select_mamo = subparsers.add_parser(
        "select-mamo-adjudication",
        help="apply MAMO Terra gates and freeze the balanced 8+4 Sol set",
    )
    select_mamo.add_argument("--campaign-dir", type=Path, required=True)
    select_mamo.add_argument("--terra-comparison", type=Path, required=True)
    select_mamo.add_argument("--seed", default="mamo-sol-adjudication-v1")

    compare_model = subparsers.add_parser("compare-model-run", help="compare terminated model runs with hidden answers")
    compare_model.add_argument("--campaign-dir", type=Path, required=True)
    compare_model.add_argument("--run-dir", type=Path, required=True)
    compare_model.add_argument("--role", choices=["terra", "sol"], required=True)

    owner = subparsers.add_parser("build-owner-packet", help="build bounded 12-row owner review packet")
    owner.add_argument("--campaign-dir", type=Path, required=True)

    owner_validate = subparsers.add_parser(
        "validate-owner-packet",
        help="validate owner-review vocabulary, completion, and material-case gate",
    )
    owner_validate.add_argument("--campaign-dir", type=Path, required=True)
    scan_industry = subparsers.add_parser(
        "scan-industryor-opened",
        help="freeze IndustryOR rows opened by prior nested Codex sessions",
    )
    scan_industry.add_argument("--experiments-root", type=Path, required=True)
    scan_industry.add_argument("--dataset", type=Path, required=True)
    scan_industry.add_argument("--out", type=Path, required=True)
    prepare_industry = subparsers.add_parser(
        "prepare-industryor-interpretation",
        help="freeze a stratified answer-blind IndustryOR interpretation denominator",
    )
    prepare_industry.add_argument("--dataset", type=Path, required=True)
    prepare_industry.add_argument("--opened-manifest", type=Path, required=True)
    prepare_industry.add_argument("--dataset-commit", required=True)
    prepare_industry.add_argument("--out-dir", type=Path, required=True)
    prepare_industry.add_argument("--seed", default="industryor-interpretation-set-v0-2026-07")
    prepare_industry.add_argument("--per-difficulty", type=int, default=8)
    evaluate_interpretation = subparsers.add_parser(
        "evaluate-interpretation-run",
        help="apply a no-answer interpretation generation gate",
    )
    evaluate_interpretation.add_argument("--run-dir", type=Path, required=True)
    evaluate_interpretation.add_argument("--out", type=Path, required=True)
    evaluate_interpretation.add_argument("--expected-rows", type=int, required=True)
    evaluate_interpretation.add_argument("--min-valid", type=int, required=True)
    evaluate_interpretation.add_argument("--min-material-multi-variant", type=int, required=True)
    compare_industry = subparsers.add_parser(
        "compare-industryor-interpretation",
        help="compare terminated baseline and interpretation-set runs with hidden answers",
    )
    compare_industry.add_argument("--campaign-dir", type=Path, required=True)
    compare_industry.add_argument("--baseline-run-dir", type=Path, required=True)
    compare_industry.add_argument("--candidate-run-dir", type=Path, required=True)
    select_interpretation = subparsers.add_parser(
        "select-interpretation-adjudication",
        help="freeze answer-blind disputed and robust-control Sol packets",
    )
    select_interpretation.add_argument("--campaign-dir", type=Path, required=True)
    select_interpretation.add_argument("--candidate-run-dir", type=Path, required=True)
    select_interpretation.add_argument("--seed", default="industryor-interpretation-sol-v0-2026-07")
    finalize_industry = subparsers.add_parser(
        "finalize-industryor-interpretation",
        help="apply Sol stability and fresh-signal route gates",
    )
    finalize_industry.add_argument("--campaign-dir", type=Path, required=True)
    finalize_industry.add_argument("--sol-run-dir", type=Path, required=True)
    return parser


def _load_override_map(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in payload.items()):
        raise NL4OPTError("override map must be a JSON object of string row keys to string source IDs")
    return payload


def _select_adjudication(args: argparse.Namespace) -> dict[str, int]:
    source_rows = {
        row["row_id"]: row
        for row in read_jsonl(args.campaign_dir / "source" / "evidence-source-manifest.jsonl")
    }
    comparisons = read_jsonl(args.terra_comparison)

    def rank(row: dict, kind: str) -> str:
        from or_ci.nl4opt_audit import sha256_text

        return sha256_text(f"{args.seed}:{kind}:{row['row_id']}")

    supported = sorted(
        [row for row in comparisons if row.get("supported_discrepancy") is True],
        key=lambda row: rank(row, "discrepancy"),
    )[: args.discrepancies]
    clean = sorted(
        [row for row in comparisons if row.get("terra_clean") is True],
        key=lambda row: rank(row, "clean"),
    )[: args.clean_controls]
    selected_ids = [row["row_id"] for row in supported + clean]
    if len(selected_ids) != len(set(selected_ids)):
        raise NL4OPTError("adjudication selection contains duplicate rows")
    manifest = [{**source_rows[row_id], "split": "sol_adjudication"} for row_id in selected_ids]
    write_jsonl(args.campaign_dir / "source" / "sol-source-manifest.jsonl", manifest)
    write_json(
        args.campaign_dir / "provenance" / "sol-selection.json",
        {
            "seed": args.seed,
            "requested_discrepancies": args.discrepancies,
            "requested_clean_controls": args.clean_controls,
            "selected_supported_discrepancies": [row["row_id"] for row in supported],
            "selected_terra_clean_controls": [row["row_id"] for row in clean],
            "selected_total": len(manifest),
            "answer_blind_manifest": "source/sol-source-manifest.jsonl",
        },
    )
    return {"supported_discrepancies": len(supported), "clean_controls": len(clean), "total": len(manifest)}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare-nl4opt":
            provenance = prepare_pilot(
                official_path=args.official,
                historical_path=args.historical,
                corrected_path=args.corrected,
                output_dir=args.out_dir,
                official_commit=args.official_commit,
                corrected_commit=args.corrected_commit,
                seed=args.seed,
                control_count=args.control_count,
                expected_answer_changes=args.expected_answer_changes,
                overrides=_load_override_map(args.override_map),
            )
            print(json.dumps(provenance["counts"], sort_keys=True))
            return 0
        if args.command == "prepare-nl4opt-census":
            provenance = prepare_nl4opt_census(
                official_path=args.official,
                historical_path=args.historical,
                corrected_path=args.corrected,
                all_official_solver_results_path=args.all_official_solver_results,
                july_pilot_campaign_dir=args.july_pilot_campaign_dir,
                output_dir=args.out_dir,
                official_commit=args.official_commit,
                corrected_commit=args.corrected_commit,
                seed=args.seed,
                overrides=_load_override_map(args.override_map),
            )
            print(json.dumps(provenance["counts"], sort_keys=True))
            return 0
        if args.command == "reconcile-nl4opt-evidence":
            result = reconcile_nl4opt_evidence(
                campaign_dir=args.campaign_dir,
                june_manifest_dir=args.june_manifest_dir,
                july_pilot_campaign_dir=args.july_pilot_campaign_dir,
                output_path=args.out,
                summary_path=args.summary_out,
            )
            print(json.dumps(result, sort_keys=True))
            return 0
        if args.command == "merge-nl4opt-census-terra":
            result = merge_nl4opt_census_terra(
                campaign_dir=args.campaign_dir,
                july_pilot_campaign_dir=args.july_pilot_campaign_dir,
                delta_comparison_path=args.delta_comparison,
                delta_run_dir=args.delta_run_dir,
                output_path=args.out,
            )
            print(json.dumps(result, sort_keys=True))
            return 0
        if args.command == "select-nl4opt-census-adjudication":
            result = select_nl4opt_census_adjudication(
                campaign_dir=args.campaign_dir,
                terra_comparison_path=args.terra_comparison,
                prior_owner_packet_path=args.prior_owner_packet,
                seed=args.seed,
                max_candidates=args.max_candidates,
            )
            print(json.dumps(result, sort_keys=True))
            return 0
        if args.command == "finalize-nl4opt-census":
            result = finalize_nl4opt_census(
                campaign_dir=args.campaign_dir,
                terra_comparison_path=args.terra_comparison,
                sol_comparison_path=args.sol_comparison,
                owner_csv_path=args.owner_csv,
                owner_status_path=args.owner_status,
                census_rows_path=args.census_rows,
                terra_run_summary_path=args.terra_run_summary,
                sol_run_summary_path=args.sol_run_summary,
                output_path=args.out,
            )
            print(json.dumps(result, sort_keys=True))
            return 0
        if args.command == "scan-mamo-opened":
            result = scan_opened_mamo_rows(
                experiments_root=args.experiments_root,
                original_path=args.original,
                output_path=args.out,
            )
            print(json.dumps(result, sort_keys=True))
            return 0
        if args.command == "prepare-mamo":
            provenance = prepare_mamo_replication(
                original_path=args.original,
                revised_path=args.revised,
                correction_manifest_path=args.correction_manifest,
                opened_manifest_path=args.opened_manifest,
                output_dir=args.out_dir,
                original_commit=args.original_commit,
                revised_commit=args.revised_commit,
                seed=args.seed,
                corrected_count=args.corrected_count,
                control_count=args.control_count,
                min_revised_recovery=args.min_revised_recovery,
                min_revision_discrimination=args.min_revision_discrimination,
                max_control_disagreement=args.max_control_disagreement,
            )
            print(json.dumps(provenance["counts"], sort_keys=True))
            return 0
        if args.command == "solve-official":
            results = solve_official_targets(load_official_targets(args.official))
            write_jsonl(args.out, results)
            failures = sum(
                result[domain]["status"] == "parse_or_solver_error"
                for result in results
                for domain in ("continuous", "integer")
            )
            print(json.dumps({"targets": len(results), "parse_or_solver_errors": failures}, sort_keys=True))
            return 1 if failures else 0
        if args.command == "solve-pilot":
            results = solve_pilot_targets(args.campaign_dir)
            print(json.dumps({"rows": len(results)}, sort_keys=True))
            return 0
        if args.command == "compare-formal":
            rows = compare_formal_target_results(args.campaign_dir)
            recovered = sum(row["formal_target_recovers_correction"] for row in rows)
            semantic_differences = sum(
                row["answer_relation"] == "semantic_difference" for row in rows
            )
            print(
                json.dumps(
                    {
                        "rows": len(rows),
                        "semantic_answer_differences": semantic_differences,
                        "formal_target_recovers_correction": recovered,
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "validate-source-manifest":
            result = validate_source_manifest(args.manifest, args.campaign_dir)
            if args.out:
                write_json(args.out, result)
            print(json.dumps(result, sort_keys=True))
            return 0 if result["status"] == "valid" else 1
        if args.command == "select-adjudication":
            print(json.dumps(_select_adjudication(args), sort_keys=True))
            return 0
        if args.command == "select-mamo-adjudication":
            result = select_mamo_adjudication(
                campaign_dir=args.campaign_dir,
                terra_comparison_path=args.terra_comparison,
                seed=args.seed,
            )
            print(json.dumps(result, sort_keys=True))
            return 0 if result["status"] == "frozen" else 1
        if args.command == "compare-model-run":
            rows = compare_model_run(campaign_dir=args.campaign_dir, run_dir=args.run_dir, role=args.role)
            print(
                json.dumps(
                    {
                        "rows": len(rows),
                        "success": sum(row["terminal_status"] == "success" for row in rows),
                        "semantic_answer_differences": sum(
                            row["answer_relation"] == "semantic_difference" for row in rows
                        ),
                        "encoding_equivalents": sum(
                            row["answer_relation"] == "encoding_equivalent" for row in rows
                        ),
                        "supported_discrepancies": sum(row["supported_discrepancy"] for row in rows),
                        "corrections_reproduced_any_domain": sum(
                            row["correction_reproduced_any_domain"] for row in rows
                        ),
                        "corrections_discriminated": sum(row["correction_discriminated"] for row in rows),
                        "revised_reproduced_selected_domain": sum(
                            row["revised_reproduced_selected_domain"] for row in rows
                        ),
                        "revised_discriminated_selected_domain": sum(
                            row["revised_discriminated_selected_domain"] for row in rows
                        ),
                        "unchanged_control_disagreement_selected_domain": sum(
                            row["unchanged_control_disagreement_selected_domain"] for row in rows
                        ),
                        "domain_ambiguous": sum(row["domain_ambiguous"] for row in rows),
                        "control_escalations": sum(row["control_escalated"] for row in rows),
                        "unsupported_control_escalations": sum(
                            row["unsupported_control_escalation"] for row in rows
                        ),
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "build-owner-packet":
            print(json.dumps(build_owner_review_packet(campaign_dir=args.campaign_dir), sort_keys=True))
            return 0
        if args.command == "validate-owner-packet":
            result = validate_owner_review_packet(campaign_dir=args.campaign_dir)
            print(json.dumps(result, sort_keys=True))
            return 0 if result["status"] == "valid_complete" else 1
        if args.command == "scan-industryor-opened":
            result = scan_opened_industryor_rows(
                experiments_root=args.experiments_root,
                dataset_path=args.dataset,
                output_path=args.out,
            )
            print(json.dumps(result, sort_keys=True))
            return 0
        if args.command == "prepare-industryor-interpretation":
            result = prepare_industryor_interpretation(
                dataset_path=args.dataset,
                opened_manifest_path=args.opened_manifest,
                output_dir=args.out_dir,
                dataset_commit=args.dataset_commit,
                seed=args.seed,
                per_difficulty=args.per_difficulty,
            )
            print(json.dumps(result, sort_keys=True))
            return 0
        if args.command == "evaluate-interpretation-run":
            result = evaluate_interpretation_run(
                run_dir=args.run_dir,
                output_path=args.out,
                expected_rows=args.expected_rows,
                min_valid=args.min_valid,
                min_material_multi_variant=args.min_material_multi_variant,
            )
            print(json.dumps(result, sort_keys=True))
            return 0 if result["authorized_next_wave"] else 1
        if args.command == "compare-industryor-interpretation":
            result = compare_industryor_runs(
                campaign_dir=args.campaign_dir,
                baseline_run_dir=args.baseline_run_dir,
                candidate_run_dir=args.candidate_run_dir,
            )
            print(json.dumps(result, sort_keys=True))
            return 0 if result["sol_authorized"] else 1
        if args.command == "select-interpretation-adjudication":
            result = select_interpretation_adjudication(
                campaign_dir=args.campaign_dir,
                candidate_run_dir=args.candidate_run_dir,
                seed=args.seed,
            )
            print(json.dumps(result, sort_keys=True))
            return 0 if result["status"] == "frozen" else 1
        if args.command == "finalize-industryor-interpretation":
            result = finalize_industryor_interpretation(
                campaign_dir=args.campaign_dir,
                sol_run_dir=args.sol_run_dir,
            )
            print(json.dumps(result, sort_keys=True))
            return 0
    except (NL4OPTError, InterpretationAuditError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
