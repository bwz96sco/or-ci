"""Parity replay: verify library detector output matches frozen campaign ledgers byte-identically."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import sys
from pathlib import Path

NOTE_ROOT = Path("/Users/zhangbowen/Projects/OR/note/OR-research/experiments")

NL4OPT_DENOMINATOR = (
    NOTE_ROOT / "packs" / "nl4opt-v3-detector-v1-replay-2026-06"
    / "campaign_outputs" / "nl4opt_v3_detector_replay_denominator.csv"
)
NL4OPT_FROZEN_LEDGER = (
    NOTE_ROOT / "packs" / "source-vs-artifact-detector-v2-regression-2026-06"
    / "detector_outputs" / "detector_v2_nl4opt_v3_ledger.csv"
)

MIPLIB_DENOMINATOR = (
    NOTE_ROOT / "packs" / "miplibnl-source-fidelity-route-qualification-v0-2026-06"
    / "route_outputs" / "miplibnl_denominator.csv"
)
MIPLIB_FROZEN_LEDGER = (
    NOTE_ROOT / "packs" / "miplibnl-detector-v2-independent-validation-2026-06"
    / "miplib_outputs" / "miplibnl_detector_v2_replay_ledger.csv"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_csv_bytes(fields: list[str], rows: list[dict], lineterminator: str = "\n") -> bytes:
    buf = io.BytesIO()
    wrapper = io.TextIOWrapper(buf, encoding="utf-8", newline="")
    writer = csv.DictWriter(wrapper, fieldnames=fields, extrasaction="ignore", lineterminator=lineterminator)
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in fields})
    wrapper.flush()
    return buf.getvalue()


def detect_line_ending(data: bytes) -> str:
    if b"\r\n" in data:
        return "\r\n"
    return "\n"


def replay_nl4opt(check: bool) -> tuple[bool, str, str]:
    from or_ci.detector.v2_rules import run_row, LEDGER_FIELDS
    denominator = read_csv(NL4OPT_DENOMINATOR)
    results = [run_row(row, "combined") for row in denominator]
    frozen_bytes = NL4OPT_FROZEN_LEDGER.read_bytes()
    le = detect_line_ending(frozen_bytes)
    replay_bytes = write_csv_bytes(LEDGER_FIELDS, results, lineterminator=le)
    replay_hash = sha256_bytes(replay_bytes)
    frozen_hash = sha256_bytes(frozen_bytes)
    passed = replay_hash == frozen_hash
    return passed, replay_hash, frozen_hash


def replay_miplib(check: bool) -> tuple[bool, str, str]:
    from or_ci.detector.miplib_rules import run_row, LEDGER_FIELDS
    denominator = read_csv(MIPLIB_DENOMINATOR)
    results = [run_row(row) for row in denominator]
    frozen_bytes = MIPLIB_FROZEN_LEDGER.read_bytes()
    le = detect_line_ending(frozen_bytes)
    replay_bytes = write_csv_bytes(LEDGER_FIELDS, results, lineterminator=le)
    replay_hash = sha256_bytes(replay_bytes)
    frozen_hash = sha256_bytes(frozen_bytes)
    passed = replay_hash == frozen_hash
    return passed, replay_hash, frozen_hash


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay detector parity check")
    parser.add_argument("--check", action="store_true", help="exit nonzero on any mismatch")
    parser.add_argument("--nl4opt-only", action="store_true")
    parser.add_argument("--miplib-only", action="store_true")
    args = parser.parse_args()

    all_pass = True

    if not args.miplib_only:
        if not NL4OPT_DENOMINATOR.is_file():
            print(f"SKIP NL4OPT: denominator not found at {NL4OPT_DENOMINATOR}")
        elif not NL4OPT_FROZEN_LEDGER.is_file():
            print(f"SKIP NL4OPT: frozen ledger not found at {NL4OPT_FROZEN_LEDGER}")
        else:
            passed, replay_hash, frozen_hash = replay_nl4opt(args.check)
            status = "PASS" if passed else "FAIL"
            print(f"NL4OPT: {status}  replay={replay_hash[:16]}  frozen={frozen_hash[:16]}")
            if not passed:
                all_pass = False

    if not args.nl4opt_only:
        if not MIPLIB_DENOMINATOR.is_file():
            print(f"SKIP MIPLIB: denominator not found at {MIPLIB_DENOMINATOR}")
        elif not MIPLIB_FROZEN_LEDGER.is_file():
            print(f"SKIP MIPLIB: frozen ledger not found at {MIPLIB_FROZEN_LEDGER}")
        else:
            passed, replay_hash, frozen_hash = replay_miplib(args.check)
            status = "PASS" if passed else "FAIL"
            print(f"MIPLIB: {status}  replay={replay_hash[:16]}  frozen={frozen_hash[:16]}")
            if not passed:
                all_pass = False

    if args.check and not all_pass:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
