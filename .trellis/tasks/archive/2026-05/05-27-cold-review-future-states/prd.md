# Harden Cold Review Future States

## Goal

Make the paper readiness and execution board builders accept future
cold-protocol review states after cold labels complete, rather than
hard-coding the initial `blocked_pending_cold_protocol_check` state. Add
self-test coverage for pending labels, pending review decision, and accepted
protocol states without fabricating real labels.

## Confirmed Facts

- Current cold intake is `pending_cold_labels`; current capstone distribution
  is `blocked_pending_cold_protocol_check`.
- The new cold-protocol review gate can later produce:
  - `blocked_pending_protocol_review_decision`;
  - `blocked_protocol_revision_required`;
  - `blocked_by_protocol_review`;
  - `ready_for_capstone_distribution`.
- `build_paper_evidence_pack_readiness.py` currently validates capstone
  distribution against the initial blocked status.
- `build_next_stage_execution_board.py` currently asserts the primary action
  must remain `complete_5_cold_check_labels`.
- Those assumptions will become stale when cold labels arrive, even before the
  overall plan is complete.

## Requirements

- Keep the current generated artifacts unchanged in meaning: no cold labels,
  no accepted decision, capstone blocked, paper `report_ready=false`.
- Update readiness logic so future capstone distribution statuses are valid
  when consistent with cold intake and cold review:
  - incomplete cold labels: capstone stays `blocked_pending_cold_protocol_check`;
  - complete cold labels plus blank decision: capstone may be
    `blocked_pending_protocol_review_decision`;
  - complete cold labels plus `revise_protocol`: capstone may be
    `blocked_protocol_revision_required`;
  - complete cold labels plus `keep_blocked`: capstone may be
    `blocked_by_protocol_review`;
  - `accept_protocol`: capstone may become
    `ready_for_human_capstone_rater_distribution`.
- Update board validation so the primary action may advance from cold labels
  to protocol decision, capstone labels, or later evidence gates as upstream
  gates complete.
- Add self-test coverage for the status transitions without editing real label
  CSVs or inventing evidence.

## Acceptance Criteria

- [x] Current-state `--check` commands still pass and keep `report_ready=false`.
- [x] Self-tests cover pending cold labels, pending protocol decision, accepted
  protocol/capstone-distribution-ready, and later report-blocked states.
- [x] Future-state checks do not require hard-coded current statuses.
- [x] No labels, model responses, mutation outcomes, or paper-ready claims are
  created.

## Notes

- This is a robustness patch for the automation around the existing review
  gate, not progress on external human evidence itself.
