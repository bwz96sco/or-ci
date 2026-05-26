# Retry baseline Oracle response smoke

## Goal

Retry the first baseline-ablation external model run under the frozen Oracle
CLI / ChatGPT Extended Pro policy and record only real evidence: either a
validated raw response for `direct_strong_llm/P001` or an updated infrastructure
failure note that proves no response was captured.

## Requirements

- Use the frozen policy in
  `baseline-model-run-policy-2026-05-27.md`.
- Use queue row `direct_strong_llm/P001` from
  `baseline-ablation-run-queue-2026-05-26.csv`.
- Submit only through Oracle CLI browser mode with model
  `gpt-5.5-pro` / ChatGPT Extended Pro.
- Preserve the queued prompt-to-response mapping:
  - prompt: `baseline-ablation-inputs-2026-05-26/direct_strong_llm/P001.md`
  - raw response:
    `baseline-ablation-raw-responses-2026-05-26/direct_strong_llm/P001.json`
- If a response is captured, store the raw model output at the queued path and
  update the response template only from that real output.
- If Oracle fails before submission or returns the wrong surface/model, record
  the failure in notes without creating a raw response or baseline decision.
- Do not infer any baseline decision from queue readiness, a failed Oracle
  attempt, or partial browser output.

## Acceptance Criteria

- [x] Oracle status/history is inspected before retrying.
- [x] Dry run or prompt assembly is checked before live submission.
- [x] Live retry is attempted under the frozen policy, or a pre-submit
      infrastructure blocker is recorded with evidence.
- [x] Either raw response JSON validates through
      `build_baseline_response_capture.py --check`, or the failure note states
      that no raw response was written.
- [x] Baseline run queue/results validators still pass.
- [x] Roadmap/reconciliation or failure note reflects the current state.
- [x] Notes repo is clean after commit.
- [x] Trellis task is archived after verification.

## Notes

- This task may capture at most one smoke response. It is not the 52-row run.
- Do not use API mode or any model/surface outside the frozen policy.
