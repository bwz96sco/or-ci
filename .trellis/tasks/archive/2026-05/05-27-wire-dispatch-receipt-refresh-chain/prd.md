# Wire dispatch receipt refresh chain

## Goal

Make post-send/return receipt refresh commands cover all generated operator surfaces without recording external evidence.

## Confirmed Facts

- The roadmap's current primary next action is the human-dependent cold
  protocol check.
- `record_human_dispatch_receipt_event.py` records only operator-entered
  send/return receipt rows and currently prints follow-up commands for the
  receipt ledger only.
- Downstream operator surfaces depend on the receipt ledger state:
  outbox preflight, human evidence tracker, next-stage execution board, paper
  readiness/draft, and smoke report.
- The work must not create a send event, returned label, accepted mutation
  seed, promoted label, final-cost value, paper-ready claim, or paper branch.

## Requirements

- Expand the post-receipt follow-up command chain so a real send/return event
  can be propagated through all generated operator surfaces.
- Keep receipt recording dry-run by default and writing only under
  `--execute`.
- Keep generated refresh commands explicit and inspectable in the recorder
  output.
- Regenerate any affected notes artifacts after the command-chain change.
- Preserve the current evidence state: no sends/returns recorded, no human
  labels created, and `report_ready=false`.

## Acceptance Criteria

- [x] `record_human_dispatch_receipt_event.py --check` passes.
- [x] `record_human_dispatch_receipt_event.py --self-test` passes.
- [x] A dry-run send preview prints follow-up commands for receipt ledger,
      outbox preflight, human tracker, execution board, paper readiness/draft,
      and smoke refresh/check.
- [x] Evidence-gate smoke passes and remains `report_ready=false`.
- [x] Existing tests still pass.
- [x] No receipt event, returned label, promoted label, final-cost value,
      report-ready claim, or final branch decision is created.

## Notes

- This task improves the operator path for external evidence collection; it
  does not perform the external evidence collection itself.
