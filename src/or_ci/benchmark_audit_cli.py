from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

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

    compare_model = subparsers.add_parser("compare-model-run", help="compare terminated model runs with hidden answers")
    compare_model.add_argument("--campaign-dir", type=Path, required=True)
    compare_model.add_argument("--run-dir", type=Path, required=True)
    compare_model.add_argument("--role", choices=["terra", "sol"], required=True)

    owner = subparsers.add_parser("build-owner-packet", help="build bounded 12-row owner review packet")
    owner.add_argument("--campaign-dir", type=Path, required=True)
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
            print(json.dumps({"rows": len(rows), "formal_target_recovers_correction": recovered}, sort_keys=True))
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
        if args.command == "compare-model-run":
            rows = compare_model_run(campaign_dir=args.campaign_dir, run_dir=args.run_dir, role=args.role)
            print(
                json.dumps(
                    {
                        "rows": len(rows),
                        "success": sum(row["terminal_status"] == "success" for row in rows),
                        "supported_discrepancies": sum(row["supported_discrepancy"] for row in rows),
                        "corrections_reproduced_any_domain": sum(
                            row["correction_reproduced_any_domain"] for row in rows
                        ),
                        "corrections_discriminated": sum(row["correction_discriminated"] for row in rows),
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
    except (NL4OPTError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
