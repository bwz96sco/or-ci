# Add evidence gate smoke runner

## Goal

Add a single operator-facing smoke runner for the OR-CI next-stage evidence
gates. The runner should verify that the existing validation scripts still
agree with their generated artifacts and that their future-state self-tests
still pass, so the roadmap can advance safely when human labels and reviews
arrive.

## Requirements

- Place the runner in the notes vault, near the paper evidence-pack readiness
  artifacts, because it coordinates multiple evidence tracks rather than core
  OR-CI package behavior.
- Run only non-mutating validation paths: `--check` and `--self-test` where
  already supported. Do not run label promotion, mutation execution, Oracle
  submission, baseline submission, or any command that creates empirical
  evidence.
- Cover the current required evidence tracks from the roadmap and review
  reconciliation: cold protocol, cold review, capstone, Phase 2 50-case,
  NL4OPT, baseline response gates, mutation seed review gates, label
  promotion readiness, human evidence tracker, paper readiness, and execution
  board.
- Write machine-readable JSON and a compact Markdown report with command
  status, failure details, elapsed time, and the current report-ready
  guardrail.
- Keep `report_ready=false` unless the existing paper-readiness and execution
  board artifacts both say the report is ready.
- Make the runner itself checkable with `--check`, failing when the committed
  smoke report is stale.
- Use deterministic local paths and `uv run python`-style command strings in
  the report for operator reproducibility.
- Preserve the non-claim boundary: the output may say which gates passed, but
  must not claim human-label completion, FAR reduction, mutation recall,
  external accuracy, or publication readiness.

## Acceptance Criteria

- [ ] A new smoke-runner script exists in the notes vault and can generate
      JSON and Markdown outputs.
- [ ] `--check` validates the committed outputs and returns nonzero if they
      are stale or any child gate fails.
- [ ] The generated report includes all covered commands, pass/fail status,
      elapsed time, and non-claim guardrails.
- [ ] The generated JSON exposes `status`, `issue_count`, `report_ready`, and
      per-command results.
- [ ] The runner avoids evidence-producing actions and only invokes existing
      `--check` / `--self-test` paths.
- [ ] Existing gate checks still pass after the runner is added.

## Notes

- This task is infrastructure for the long-term research plan. It does not
  satisfy the external evidence blockers by itself.
