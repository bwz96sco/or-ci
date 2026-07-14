# Design: Evidence Gate Smoke Runner

## Boundary

The runner lives in
`/Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/or-ci-paper-evidence-pack-2026-05-27/`
because it aggregates evidence readiness across labeling operations,
self-host exploration, and paper-readiness artifacts.

It is a coordination validator, not an evidence generator. It invokes only
existing `--check` and `--self-test` entry points and writes a report about
their status.

## Data Flow

1. Define a fixed registry of child commands.
2. Execute each command with the current Python interpreter from the notes
   vault root, while recording the reproducible display command using
   `PYTHONDONTWRITEBYTECODE=1 uv run python ...`.
3. Read the existing paper-readiness and next-stage board JSON artifacts.
4. Compute summary fields:
   - `status`: `all_smoke_gates_passed` or `smoke_gate_failures`
   - `issue_count`: failed child command count plus source-artifact issues
   - `report_ready`: true only when both existing readiness sources are true
   - `report_ready_sources`: copied source values
5. Write `evidence-gate-smoke-report-2026-05-27.json` and `.md`.
6. In `--check`, compare generated output to committed files and fail on drift
   or any child failure.

## Command Scope

The registry covers:

- labeling operations rater-bundle distribution checks
- rater packet leakage audit check/self-test
- cold/capstone/Phase2/NL4OPT intake checks and self-tests
- cold protocol dispatch and review gates
- human tracker and handoff gates
- label promotion readiness check only
- baseline response capture/intake/results/operator checks and self-tests
- mutation seed review/operator/intake checks and self-tests
- paper evidence-pack readiness and next-stage execution board checks/self-tests

Excluded commands:

- `--execute` promotion
- mutation generation or mutation work queue execution
- Oracle/model submission
- rater packet generation unless covered by an existing check-only script

## Compatibility

Existing scripts already expose the relevant local CLI contracts. The runner
should use subprocess boundaries instead of importing every script, because
importing cross-directory modules would entangle unrelated script globals and
working-directory assumptions.

## Failure Mode

A child failure becomes a smoke-report issue. The Markdown report should show
the failed command and a compact tail of stdout/stderr so the next operator can
rerun the exact command.
