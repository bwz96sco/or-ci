# Parallel dispatch receipt refresh design

## Boundary

Patch the notes-vault parallel dispatch builder:

- `experiments/packs/or-ci-labeling-operations-2026-05-26/build_parallel_human_dispatch_send_packets.py`

Regenerate:

- `parallel-human-dispatch-send-packets-2026-05-27.json`
- `parallel-human-dispatch-send-packets-2026-05-27.md`
- smoke report artifacts if elapsed/check output changes

## Data Flow

Each parallel packet already contains:

- the outbound coordinator/rater message;
- dry-run and `--execute` receipt recorder commands;
- an expected receipt-event row template.

Add the canonical refresh chain from
`record_human_dispatch_receipt_event.FOLLOW_UP_COMMANDS` to each packet so the
operator can update derived surfaces after a real send without hunting through
separate docs.

## Guardrails

- Do not run recorder commands with `--execute`.
- Do not modify receipt-events CSV or staged label CSVs.
- Do not mark mutation seeds accepted.
- Keep paper readiness blocked.

