from __future__ import annotations

import argparse
from pathlib import Path

from or_ci.metadata import MetadataError
from or_ci.report import write_report
from or_ci.verifier import verify


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "verify":
        return _verify_command(args)
    parser.print_help()
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="or-ci")
    subparsers = parser.add_subparsers(dest="command", required=True)

    verify_parser = subparsers.add_parser("verify", help="verify a handwritten OR model submission")
    verify_parser.add_argument("--problem", required=True, type=Path)
    verify_parser.add_argument("--submission", required=True, type=Path)
    verify_parser.add_argument("--out", required=True, type=Path)
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


if __name__ == "__main__":
    raise SystemExit(main())
