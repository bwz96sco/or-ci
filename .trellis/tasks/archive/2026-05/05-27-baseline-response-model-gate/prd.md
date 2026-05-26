# Harden baseline response model gate

## Goal

Harden the baseline ablation response-capture and results validators so a
completed baseline response can only pass if its recorded model/tool metadata
matches the frozen run-queue policy for ChatGPT Extended Pro / GPT-5.5 Pro
thinking-heavy.

## Requirements

- Add deterministic validation that compares every completed response-template
  row against the corresponding `baseline-ablation-run-queue-2026-05-26.csv`
  `ledger_model_or_tool` and `ledger_model_version` values.
- Surface expected and recorded model metadata in the response-capture
  readiness CSV so wrong-mode captures are diagnosable.
- Reject any completed baseline response row whose model/tool or model version
  is missing or differs from the frozen run-queue policy.
- Preserve current evidence state: do not create raw model responses, do not
  fill response-template decisions, and do not infer baseline results from
  previous failed Oracle attempts.
- Update baseline policy/runbook text if needed so the capture workflow states
  that Pro/Instant/other model labels must not be accepted under the Extended
  Pro baseline queue.

## Acceptance Criteria

- [x] `build_baseline_response_capture.py --check` passes.
- [x] `build_baseline_response_capture.py --self-test` proves malformed JSON,
      orphan raw responses, and model-policy mismatches are rejected.
- [x] `build_baseline_ablation_results.py --check` passes and enforces the same
      frozen model metadata for completed rows.
- [x] Baseline capture readiness still reports 52 expected responses, 0 present
      raw responses, 0 completed template rows, and 0 issues.
- [x] Baseline results summary still reports 52 pending rows and 0 completed
      rows.
- [x] No raw responses, baseline decisions, human labels, mutation outcomes, or
      paper-ready claims are created.
- [x] Notes changes are committed; Trellis task is archived after verification.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
