# Human dispatch receipt events intake

## Goal

Add an operator-editable receipt-events intake CSV and merge it into the generated human dispatch receipt ledger without creating labels or claims.

## Requirements

- Extend the notes-side receipt ledger generator:
  `experiments/or-ci-labeling-operations-2026-05-26/build_human_dispatch_receipt_ledger.py`.
- Add an operator-editable receipt-events CSV:
  `human-dispatch-receipt-events-2026-05-27.csv`.
- The events CSV must be created as a stable template and then preserved on
  later generator runs so operator-entered send/return events are not
  overwritten.
- Merge event rows into the generated receipt ledger by `wave_id`.
- Support these event fields:
  - `wave_id`;
  - `receipt_status`;
  - `sent_at`;
  - `sent_by`;
  - `returned_at`;
  - `returned_file_sha256`;
  - `receipt_note`.
- Validate impossible event states, including unknown wave ids, duplicate
  wave ids, blocked rows with send/return data, returned rows without send
  data, and validated rows without a returned checksum.
- Preserve the default current state: no sends, no returns, no validations,
  and `report_ready=false`.
- Update JSON/Markdown output to cite the receipt-events CSV as the editable
  source for operator receipt changes.
- Keep the existing smoke-gate command count stable unless a new command is
  required; the existing receipt-ledger check/self-test should cover event
  intake.
- Preserve all no-label/no-claim constraints.

## Acceptance Criteria

- [x] `human-dispatch-receipt-events-2026-05-27.csv` exists with one row per
      dispatch wave and blank editable event fields.
- [x] The receipt-ledger generator preserves an existing events CSV instead
      of overwriting it.
- [x] The generated receipt ledger reads the events CSV and still reports
      7 rows, 0 sent, 0 returned, and 0 validated in the current state.
- [x] `build_human_dispatch_receipt_ledger.py --check` passes.
- [x] `build_human_dispatch_receipt_ledger.py --self-test` covers invalid
      receipt-event rows.
- [x] `build_evidence_gate_smoke_report.py --check` passes.
- [x] Existing dispatch wave, tracker, handoff, dashboard, paper readiness,
      execution board, and smoke checks still pass.
- [x] The task creates no human labels, model responses, mutation outcomes,
      accepted seeds, adjudication decisions, or report-ready claims.

## Notes

- This is a live-operations intake path only. It enables a future operator to
  record actual sends/returns without editing generated ledger artifacts.
- Outcome: the receipt ledger now reads preserved operator events from
  `human-dispatch-receipt-events-2026-05-27.csv`. The template has seven
  blank event rows; the generated ledger remains 7 rows, 0 sent, 0 returned,
  0 validated, and `report_ready=false`.
