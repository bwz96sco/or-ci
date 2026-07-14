# Human dispatch receipt ledger

## Goal

Add a notes-side generated receipt ledger for human dispatch waves so send/return/validation status can be tracked without creating evidence or report claims.

## Requirements

- Add a notes-side generator under
  `experiments/packs/or-ci-labeling-operations-2026-05-26/`.
- Read the generated human dispatch wave plan as the source of truth for wave
  order, sendable packages, return targets, validation commands, blockers, and
  guardrails.
- Generate deterministic CSV, JSON, and Markdown receipt-ledger artifacts.
- Include receipt bookkeeping fields for each wave:
  - receipt status;
  - recipient role;
  - sent timestamp/by;
  - returned timestamp;
  - returned file checksum;
  - validation status;
  - validation command;
  - blocker and non-claim guardrail.
- The generated current ledger must represent the current authoritative state:
  all sends and returns are pending or blocked; no labels, seed decisions,
  validation passes, or empirical outcomes are created.
- Validate that pending/blocked receipt rows do not contain completed send,
  return, checksum, or validation fields.
- Validate referenced packages, dispatch artifacts, return targets, and
  validation scripts.
- Add a self-test that rejects impossible receipt states, such as returned
  rows without a send timestamp or validated rows without a returned checksum.
- Wire the receipt-ledger check and self-test into the evidence-gate smoke
  report.
- Update roadmap/reconciliation/sync notes to reference the receipt ledger as
  coordination bookkeeping, not empirical evidence.
- Preserve existing no-label/no-claim constraints.

## Acceptance Criteria

- [x] `human-dispatch-receipt-ledger-2026-05-27.csv`,
      `human-dispatch-receipt-ledger-2026-05-27.json`, and
      `human-dispatch-receipt-ledger-2026-05-27.md` are generated.
- [x] The receipt ledger has one row per dispatch wave, including the report
      hold wave.
- [x] `build_human_dispatch_receipt_ledger.py --check` passes and detects
      stale artifacts.
- [x] `build_human_dispatch_receipt_ledger.py --self-test` passes.
- [x] `build_evidence_gate_smoke_report.py --check` includes the receipt
      ledger and passes.
- [x] Existing dispatch wave, tracker, handoff, dashboard, paper readiness,
      execution board, and smoke checks still pass.
- [x] The task creates no human labels, model responses, mutation outcomes,
      accepted seeds, adjudication decisions, or report-ready claims.

## Notes

- This is coordination infrastructure only. Actual sends and returned evidence
  still require external human action and staged intake validators.
- Outcome: added `build_human_dispatch_receipt_ledger.py`, generated a
  seven-row receipt ledger, wired its check and self-test into the smoke
  report, and refreshed the roadmap/reconciliation/sync notes. The smoke
  report now checks 60 non-mutating commands and remains `report_ready=false`.
