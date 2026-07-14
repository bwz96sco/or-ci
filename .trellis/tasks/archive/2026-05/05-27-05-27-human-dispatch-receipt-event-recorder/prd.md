# Human dispatch receipt event recorder

## Goal

Add a guarded notes-side CLI for recording real human-dispatch receipt events after an actual send or return, with validation and self-tests, without creating any send event by default.

## Confirmed Facts

- The active research plan is blocked on human evidence collection, with
  `cold_protocol_check` as the primary next track and `report_ready=false`.
- The current operator-editable receipt file is
  `experiments/packs/or-ci-labeling-operations-2026-05-26/human-dispatch-receipt-events-2026-05-27.csv`.
- Generated receipt-ledger files must not be edited directly.
- The cold-protocol send packet provides a copy-ready outgoing message but
  intentionally does not record a send.
- Any actual send/return entry must remain bookkeeping only. It must not create
  labels, promote staged labels, accept mutation seeds, adjudicate decisions,
  or advance paper claims.

## Requirements

- Add a notes-side guarded recorder CLI under
  `experiments/packs/or-ci-labeling-operations-2026-05-26/`.
- The CLI must support a dry-run preview by default and require an explicit
  `--execute` flag before mutating the receipt-events CSV.
- It must record a sent event for a selected wave only when:
  - the wave exists in the dispatch wave plan;
  - the current receipt event row is blank or still pending;
  - `sent_at` and `sent_by` are provided;
  - the requested transition is valid for the target wave state.
- It must record a returned event only when:
  - an existing sent event is present;
  - `returned_at` and `returned_file_sha256` are provided;
  - the returned checksum is a valid SHA-256 hex digest;
  - the requested status is one of the ledger-supported return states.
- It must preserve the CSV header and every unrelated wave row exactly in
  logical content.
- It must refuse blocked waves, unknown wave IDs, duplicate wave IDs, invalid
  statuses, malformed timestamps, malformed checksums, and incomplete
  transitions.
- It must print the exact row it would write plus the follow-up ledger
  regeneration/check commands.
- It must provide `--check` and `--self-test` modes that are non-mutating.
- Wire the recorder self-test into the evidence-gate smoke report.
- Update roadmap/sync notes to point to the recorder as the safe way to record
  an actual send or return after the coordinator has performed that external
  action.

## Acceptance Criteria

- [x] `record_human_dispatch_receipt_event.py --help` documents send,
      return, dry-run, execute, check, and self-test behavior.
- [x] Dry-run send preview for `wave_01_cold_protocol_check` prints a
      `sent_pending_return` row but leaves
      `human-dispatch-receipt-events-2026-05-27.csv` unchanged.
- [x] `--execute` is the only mode that writes an event row.
- [x] The recorder refuses blocked waves and invalid send/return transitions.
- [x] `record_human_dispatch_receipt_event.py --check` passes on the current
      blank receipt-events CSV.
- [x] `record_human_dispatch_receipt_event.py --self-test` passes.
- [x] `build_human_dispatch_receipt_ledger.py --check` still passes and still
      reports zero sent rows in the current state.
- [x] `build_evidence_gate_smoke_report.py --check` includes the recorder
      self-test and passes.
- [x] The task creates no send event, returned evidence, human labels, model
      responses, mutation outcomes, accepted seeds, adjudication decisions, or
      report-ready claims.

## Notes

- GitNexus impact for `command_specs` returned target-not-found / UNKNOWN.
  Practical blast radius is the generated notes-vault smoke report and
  receipt-event bookkeeping artifacts, not indexed OR-CI verifier symbols.
