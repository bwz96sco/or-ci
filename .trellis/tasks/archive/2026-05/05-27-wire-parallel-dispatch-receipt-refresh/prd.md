# Wire parallel dispatch receipt refresh guidance

## Goal

Apply the receipt refresh chain to parallel-safe human dispatch packets without
recording sends or labels.

## Confirmed Facts

- The parallel-safe waves are Phase 2 labels, NL4OPT external labels, and
  mutation seed review.
- `record_human_dispatch_receipt_event.py` now exposes a full follow-up refresh
  chain after real send/return events.
- `parallel-human-dispatch-send-packets-2026-05-27.md` currently prints the
  guarded receipt recorder commands for each parallel wave, but not the full
  post-receipt refresh chain.
- Current evidence state must remain unchanged: no sends, no returned labels,
  no seed acceptances, no promoted labels, and `report_ready=false`.

## Requirements

- Update the parallel human dispatch packet builder so each packet includes
  the shared post-receipt refresh command chain.
- Reuse the canonical receipt recorder follow-up command list instead of
  duplicating a separate command sequence.
- Regenerate `parallel-human-dispatch-send-packets-2026-05-27.{json,md}` and
  any smoke artifacts affected by the check output.
- Preserve all non-claim guardrails and current evidence counts.

## Acceptance Criteria

- [x] `build_parallel_human_dispatch_send_packets.py --check` passes.
- [x] `build_parallel_human_dispatch_send_packets.py --self-test` passes.
- [x] Parallel send-packet JSON contains receipt follow-up commands for each
      included track.
- [x] Parallel send-packet Markdown lists the full refresh chain after the
      receipt recorder command for each included track.
- [x] Evidence-gate smoke passes and remains `report_ready=false`.
- [x] Existing tests still pass.
- [x] No send event, return event, human label, promoted label, mutation seed
      acceptance, final-cost value, report-ready claim, or final branch
      decision is created.

## Notes

- This is operator guidance wiring only.
