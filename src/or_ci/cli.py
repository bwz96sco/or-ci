from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import csv

from or_ci.evidence_batch import run_evidence_batch
from or_ci.evidence_pack import build_evidence_pack, write_evidence_pack
from or_ci.metadata import MetadataError, load_problem_metadata
from or_ci.report import write_report
from or_ci.verifier import verify


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "verify":
        return _verify_command(args)
    if args.command == "evidence-batch":
        return _evidence_batch_command(args)
    if args.command == "evidence-pack":
        return _evidence_pack_command(args)
    if args.command == "validate-spec":
        return _validate_spec_command(args)
    if args.command == "detect":
        return _detect_command(args)
    parser.print_help()
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="or-ci")
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_parser = subparsers.add_parser("verify", help="verify a handwritten OR model submission")
    verify_parser.add_argument("--problem", required=True, type=Path)
    verify_parser.add_argument("--submission", required=True, type=Path)
    verify_parser.add_argument("--out", required=True, type=Path)

    evidence_parser = subparsers.add_parser("evidence-pack", help="write a source-linked OR-CI evidence pack")
    evidence_parser.add_argument("--statement", required=True, type=Path)
    evidence_parser.add_argument("--problem", required=True, type=Path)
    evidence_parser.add_argument("--submission", required=True, type=Path)
    evidence_parser.add_argument("--out", required=True, type=Path)

    batch_parser = subparsers.add_parser("evidence-batch", help="write source-linked OR-CI evidence packs from a manifest")
    batch_parser.add_argument("--manifest", required=True, type=Path)
    batch_parser.add_argument("--out-dir", required=True, type=Path)
    batch_parser.add_argument("--manual-constraints", type=Path)

    validate_parser = subparsers.add_parser("validate-spec", help="validate OR-CI problem metadata")
    validate_parser.add_argument("--problem", required=True, type=Path)

    detect_parser = subparsers.add_parser("detect", help="run source-fidelity detector on a manifest or corpus")
    detect_parser.add_argument("--mode", required=True, choices=["layer0", "v1", "v2", "combined", "miplib"])
    detect_parser.add_argument("--manifest", type=Path, help="denominator CSV with per-row paths")
    detect_parser.add_argument("--corpus", type=str, help="corpus name for text-only sweep")
    detect_parser.add_argument("--data-root", type=Path, help="dataset directory (required with --corpus)")
    detect_parser.add_argument("--out-dir", required=True, type=Path)
    return parser


def _verify_command(args: argparse.Namespace) -> int:
    if not args.problem.is_file():
        raise SystemExit(f"problem file does not exist: {args.problem}")
    if not args.submission.is_file():
        raise SystemExit(f"submission file does not exist: {args.submission}")
    try:
        report = verify(args.problem, args.submission)
    except MetadataError as exc:
        raise SystemExit(f"invalid problem metadata: {exc}") from exc
    write_report(report, args.out)
    return 0


def _evidence_pack_command(args: argparse.Namespace) -> int:
    if not args.statement.is_file():
        raise SystemExit(f"statement file does not exist: {args.statement}")
    if not args.problem.is_file():
        raise SystemExit(f"problem file does not exist: {args.problem}")
    if not args.submission.is_file():
        raise SystemExit(f"submission file does not exist: {args.submission}")
    try:
        report = verify(args.problem, args.submission)
        pack = build_evidence_pack(args.statement, args.problem, args.submission, report)
    except MetadataError as exc:
        raise SystemExit(f"invalid problem metadata: {exc}") from exc
    write_evidence_pack(pack, args.out)
    return 0


def _evidence_batch_command(args: argparse.Namespace) -> int:
    if not args.manifest.is_file():
        raise SystemExit(f"manifest file does not exist: {args.manifest}")
    if args.manual_constraints is not None and not args.manual_constraints.is_file():
        raise SystemExit(f"manual constraints file does not exist: {args.manual_constraints}")
    summary = run_evidence_batch(args.manifest, args.out_dir, manual_constraints_path=args.manual_constraints)
    print(f"wrote evidence batch: {summary['succeeded']} succeeded, {summary['failed']} failed")
    return 0


def _validate_spec_command(args: argparse.Namespace) -> int:
    if not args.problem.is_file():
        print(f"problem file does not exist: {args.problem}", file=sys.stderr)
        return 1
    try:
        metadata = load_problem_metadata(args.problem)
    except (json.JSONDecodeError, MetadataError) as exc:
        print(f"invalid problem metadata: {exc}", file=sys.stderr)
        return 1
    print(f"valid problem metadata: {metadata.id}")
    return 0


def _detect_command(args: argparse.Namespace) -> int:
    if not args.manifest and not args.corpus:
        print("error: provide --manifest or --corpus", file=sys.stderr)
        return 2
    if args.manifest and args.corpus:
        print("error: provide --manifest or --corpus, not both", file=sys.stderr)
        return 2
    if args.corpus and not args.data_root:
        print("error: --data-root required with --corpus", file=sys.stderr)
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)

    if args.manifest:
        if not args.manifest.is_file():
            raise SystemExit(f"manifest file does not exist: {args.manifest}")
        return _detect_manifest(args.manifest, args.mode, args.out_dir)

    from or_ci.corpora import load_corpus
    if args.mode not in {"layer0", "v1"}:
        print(f"error: --corpus only supports layer0 or v1 text modes, got {args.mode}", file=sys.stderr)
        return 2
    rows = load_corpus(args.corpus, args.data_root)
    return _detect_corpus(rows, args.mode, args.out_dir)


def _detect_manifest(manifest: Path, mode: str, out_dir: Path) -> int:
    with manifest.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    if mode == "miplib":
        from or_ci.detector.miplib_rules import run_row as miplib_run_row, LEDGER_FIELDS
        results = [miplib_run_row(row) for row in rows]
    else:
        from or_ci.detector.v2_rules import run_row as v2_run_row, LEDGER_FIELDS
        results = [v2_run_row(row, mode) for row in rows]

    ledger_path = out_dir / "detector_ledger.csv"
    with ledger_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=LEDGER_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for result in results:
            writer.writerow({field: result.get(field, "") for field in LEDGER_FIELDS})

    detected = sum(1 for r in results if r.get("detected_fault") == "true")
    summary = {
        "mode": mode,
        "total_rows": len(results),
        "detected": detected,
        "clean": len(results) - detected,
    }
    summary_path = out_dir / "detector_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"detect: {len(results)} rows, {detected} faults detected → {out_dir}")
    return 0


def _detect_corpus(rows: list[dict], mode: str, out_dir: Path) -> int:
    from or_ci.detector.layer0_rules import detect_source_text as layer0_detect, LEDGER_FIELDS as L0_FIELDS
    from or_ci.detector.v1_rules import detect_source_text as v1_detect

    results: list[dict] = []
    for row in rows:
        text = row.get("en_question", "")
        if mode == "layer0":
            hits = layer0_detect(text)
        else:
            hits = v1_detect(text)

        detected = bool(hits)
        results.append({
            "row_id": row["row_id"],
            "dataset": row.get("dataset", ""),
            "label": row.get("label", ""),
            "detector_decision": "source_fault_detected" if detected else "no_source_fault_detected",
            "detected_fault": str(detected).lower(),
            "rule_hits": ";".join(item["rule_id"] for item in hits),
            "primary_fault_type": hits[0]["fault_type"] if hits else "",
            "evidence_quotes": " | ".join(item["evidence"] for item in hits),
            "trace_json": json.dumps(hits, sort_keys=True),
            "used_row_id_logic": "false",
            "source_hash_matches": "n/a",
            "expected_label": "",
            "case_pass": "",
            "notes": f"corpus text-only sweep mode={mode}",
        })

    fields = L0_FIELDS
    ledger_path = out_dir / "detector_ledger.csv"
    with ledger_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for result in results:
            writer.writerow({field: result.get(field, "") for field in fields})

    detected_count = sum(1 for r in results if r.get("detected_fault") == "true")
    summary = {
        "mode": mode,
        "total_rows": len(results),
        "detected": detected_count,
        "clean": len(results) - detected_count,
    }
    summary_path = out_dir / "detector_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"detect: {len(results)} rows, {detected_count} faults detected → {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
