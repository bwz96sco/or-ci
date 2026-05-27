# Wire dispatch outbox into execution surfaces

## Goal

Make the guarded human-dispatch outbox preflight visible in the main
operator-facing surfaces: the human-evidence collection tracker and the
next-stage execution board.

## Requirements

- Update the human evidence collection tracker to read
  `human-dispatch-outbox-preflight-2026-05-27.json`.
- Include outbox status, safe-to-send count, safe-to-assign-review count,
  blocked count, issue count, and per-track preflight statuses in the tracker
  JSON and Markdown.
- Update the tracker Markdown to tell the operator to require the relevant
  outbox row to be safe before external send/assignment.
- Update the next-stage execution board to read the outbox preflight and expose
  its status/counts in JSON and Markdown.
- Include the outbox preflight artifact in board proof/source references for
  human-dispatch rows.
- Regenerate dependent tracker, wave plan, receipt ledger, outbox preflight,
  execution board, paper draft, and smoke artifacts as needed.
- Preserve non-claim rules: do not send packages, record receipt events,
  create labels, promote labels, accept mutation seeds, adjudicate evidence, or
  change paper readiness.

## Acceptance Criteria

- [x] `build_human_evidence_collection_tracker.py --check` passes.
- [x] `build_next_stage_execution_board.py --check` passes.
- [x] Tracker JSON includes outbox status/counts and per-track preflight
      statuses.
- [x] Tracker Markdown cites the outbox preflight as the pre-send guard.
- [x] Execution board JSON includes outbox status/counts.
- [x] Execution board Markdown/source artifacts reference the outbox preflight.
- [x] Evidence-gate smoke passes and remains `report_ready=false`.
- [x] Existing tests still pass.
- [x] No send event, returned evidence, human label, mutation seed acceptance,
      adjudication, report-ready claim, or final branch decision is created.

## Notes

- This is a dependency-wiring task, not a new evidence-collection event.
