# Implementation Plan

## Checklist

- [x] Run GitNexus impact analysis before editing `cli.py` and before adding the new evidence-pack entry points.
- [x] Add `src/or_ci/evidence_pack.py`.
- [x] Add `evidence-pack` parser branch to `src/or_ci/cli.py`.
- [x] Add tests in `tests/or_ci/test_cli.py` or a focused `test_evidence_pack.py`.
- [x] Run focused tests for the new command.
- [x] Run `uv run pytest`.
- [x] Run GitNexus `detect-changes` before committing.

## Expected Files

- `src/or_ci/evidence_pack.py`
- `src/or_ci/cli.py`
- `tests/or_ci/test_cli.py` or `tests/or_ci/test_evidence_pack.py`
- `.trellis/tasks/06-11-end-to-end-or-ci-adapter/*`

## Validation Commands

```bash
uv run pytest tests/or_ci/test_cli.py
uv run pytest
git diff --check
```

## Rollback Points

- If the CLI shape conflicts with existing command behavior, remove only the `evidence-pack` branch and keep `verify`/`validate-spec` untouched.
- If evidence-pack schema becomes too large, keep only hashes, paths, report, and boundary fields for this MVP.

## Review Notes

- Do not add LLM/provider/network code.
- Do not parse natural language.
- Do not introduce NL4OPT/NL4OR names in OR-CI code/tests.
- Do not claim source-statement correctness from OR-CI `PASS`.
