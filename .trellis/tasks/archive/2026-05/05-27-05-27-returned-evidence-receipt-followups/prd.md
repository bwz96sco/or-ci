# Returned evidence receipt follow-up commands

## Goal

Extend returned-evidence staging previews so operators get the correct receipt-return bookkeeping command after staging external returned CSVs, without creating sends, returns, labels, or report-ready claims.

## Requirements

- Extend the existing returned-evidence staging helper in the notes vault.
- Preserve dry-run default behavior and the existing `--execute` requirement
  before copying returned CSVs.
- After a valid staging preview or execute, print receipt-bookkeeping guidance
  that connects the staged return to the existing guarded receipt-event
  recorder.
- For single-file return tracks, print the exact dry-run command for recording
  the returned artifact with the staged/source file SHA-256:
  - `cold_protocol_check`;
  - `mutation_seed_review`.
- For split-label tracks with more than one returned file per dispatch wave,
  do not invent a single-file receipt event. Print a clear note that the
  dispatch-wave return receipt must be recorded only after the complete
  returned package/file set is available:
  - `capstone_rater_a`;
  - `capstone_rater_b`;
  - `phase2_50case_rater_a`;
  - `phase2_50case_rater_b`;
  - `nl4opt_rater_a`;
  - `nl4opt_rater_b`.
- The printed receipt command must remain dry-run by default and must not add
  `--execute`.
- Do not record send events, return events, labels, adjudications, seed
  acceptances, protocol decisions, or report-ready claims.
- Keep existing staging validation behavior: header compatibility, row count,
  ID order, fixed schema/rater fields, optional source SHA-256, blank target
  protection, placeholder rejection, and generated-readiness artifact
  rejection.
- Update the staging helper self-test so the new receipt guidance is covered.
- Regenerate any smoke report artifacts if the helper output/check behavior
  changes.

## Acceptance Criteria

- [x] A valid dry-run for `cold_protocol_check` prints a dry-run
      `record_human_dispatch_receipt_event.py --event returned` command with
      wave id `wave_01_cold_protocol_check` and the returned CSV SHA-256.
- [x] A valid dry-run for `mutation_seed_review` prints a dry-run
      `record_human_dispatch_receipt_event.py --event returned` command with
      wave id `wave_06_mutation_seed_review` and the returned CSV SHA-256.
- [x] A valid dry-run for a split-label target prints a no-single-file receipt
      note rather than a misleading returned-event command.
- [x] `stage_returned_human_evidence.py --check` passes.
- [x] `stage_returned_human_evidence.py --self-test` passes and covers both
      receipt command and split-label note behavior.
- [x] Evidence-gate smoke still passes with `report_ready=false`.
- [x] Existing intake, receipt, paper-readiness, execution-board, and project
      tests still pass.
- [x] Current source state remains unchanged: no send event, return event,
      returned evidence, labels, mutation outcome, accepted seed, adjudication,
      protocol-review decision, or report-ready claim is created.

## Notes

- This is a notes-side operator-safety improvement. It must not simulate a
  returned artifact.
