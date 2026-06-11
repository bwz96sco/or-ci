# Implementation Plan

## Checklist

- [x] Run impact analysis before editing existing symbols in `cli.py` and `evidence_pack.py` if needed.
- [x] Add `src/or_ci/formulation_adapter.py`.
- [x] Add `src/or_ci/evidence_batch.py`.
- [x] Add `evidence-batch` parser and command branch to `src/or_ci/cli.py`.
- [x] Add focused tests for:
  - existing OR-CI input manifest rows;
  - linear formulation manifest rows;
  - unsupported formulation rows that are ledgered without aborting the batch.
- [x] Run focused tests.
- [x] Run `uv run pytest`.
- [x] Run `git diff --check`.
- [x] Run Trellis/GitNexus changed-scope check before commit if available.

## Expected Files

- `src/or_ci/formulation_adapter.py`
- `src/or_ci/evidence_batch.py`
- `src/or_ci/cli.py`
- `tests/or_ci/test_evidence_batch.py`
- `.trellis/tasks/06-11-06-11-nl4opt-external-or-ci-adapter/*`

## Validation Commands

```bash
uv run pytest tests/or_ci/test_evidence_batch.py tests/or_ci/test_cli.py
uv run pytest
git diff --check
```

## Research Handoff After Coding

After OR-CI tests pass, create the actual external research manifest in OR-research from the current external formulation ledger, run `or-ci evidence-batch`, and add the resulting ledger/summary to the research evidence pack. Keep that output in OR-research, not in OR-CI tests or fixtures.

Status: completed. The OR-research batch manifest, batch outputs, and result
audit now exist under the external dataset experiment pack.

Changed-scope note: `npx gitnexus detect-changes --repo or-ci` reported HIGH
risk because the CLI dispatch file changed and participates in multiple flows.
The reviewed change is an additive `evidence-batch` command branch; existing
commands are untouched, and the full project test suite passes.

## Rollback Points

- If formulation materialization proves too broad, keep the existing-input batch path and record formulation rows as unsupported.
- If batch CLI conflicts with existing commands, remove only the `evidence-batch` branch and keep `verify`, `validate-spec`, and `evidence-pack` untouched.
