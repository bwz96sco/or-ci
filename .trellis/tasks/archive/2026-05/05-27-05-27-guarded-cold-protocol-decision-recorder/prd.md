# Guarded cold protocol decision recorder

## Goal

Add a dry-run-first recorder for the cold-protocol review decision so a
coordinator can record `accept_protocol`, `revise_protocol`, or `keep_blocked`
only after the cold-check intake gate is ready, without manual CSV edits or
premature capstone distribution.

## Confirmed Facts

- The cold-protocol review gate already reads
  `cold-protocol-review-2026-05-27/protocol-review-decision.csv`.
- The current decision row is blank and the review gate status is
  `blocked_pending_cold_labels`.
- The 13-case capstone distribution remains blocked unless the cold intake is
  `ready_for_protocol_review` and the review decision is `accept_protocol`.
- Existing receipt/event recorders use dry-run by default and require
  `--execute` to mutate operator-editable CSV files.

## Requirements

- Add a notes-side script under
  `experiments/packs/or-ci-labeling-operations-2026-05-26/`.
- Default behavior must preview a proposed decision row and change no files.
- `--execute` is required before writing
  `cold-protocol-review-2026-05-27/protocol-review-decision.csv`.
- The recorder must accept exactly one decision:
  - `accept_protocol`;
  - `revise_protocol`;
  - `keep_blocked`.
- It must require real non-placeholder values for `protocol_version`,
  `reviewer_id`, `reviewed_at`, and `rationale`.
- It must require `affected_labels_to_restart` when decision is
  `revise_protocol`.
- It must refuse to record any nonblank decision while the cold intake gate is
  not `ready_for_protocol_review`.
- It must refuse to overwrite an existing nonblank protocol-review decision.
- After a valid execute, it should tell the operator to regenerate/check the
  cold protocol review gate and downstream blockers.
- Add `--check` mode for the current decision CSV and `--self-test` mode for
  valid/invalid transition coverage.
- Wire `--check` and `--self-test` into the evidence-gate smoke report.
- Preserve all no-label/no-send/no-claim constraints.

## Acceptance Criteria

- [x] `record_cold_protocol_review_decision.py` exists.
- [x] Dry-run preview of a decision while cold intake is currently blocked is
      rejected and leaves the decision CSV unchanged.
- [x] `--check` passes on the current blank decision row.
- [x] `--self-test` passes and covers accepted, revise-without-restart,
      keep-blocked, blocked-intake, and overwrite cases.
- [x] The evidence-gate smoke report includes recorder check/self-test and
      passes with `report_ready=false`.
- [x] Existing cold review, capstone distribution, receipt ledger, execution
      board, and paper-readiness checks still pass.
- [x] The task creates no protocol-review decision, send event, returned
      evidence, labels, mutation outcome, accepted seed, adjudication decision,
      or report-ready claim.

## Notes

- This recorder is for the future post-cold-check transition. Current state
  should remain blocked because no cold labels have been returned.
