# Dispatch receipt refresh design

## Boundary

Patch the notes-vault receipt recorder:

- `experiments/or-ci-labeling-operations-2026-05-26/record_human_dispatch_receipt_event.py`

Regenerate affected generated notes artifacts if their command snapshots or
smoke outputs change.

## Data Flow

The receipt-events CSV is operator-editable source state. After a coordinator
records a real send/return with the guarded recorder, the derived surfaces must
be rebuilt in dependency order:

1. receipt ledger;
2. outbox preflight;
3. human evidence tracker;
4. paper readiness;
5. paper draft;
6. next-stage execution board;
7. evidence-gate smoke report.

The recorder should not run these commands automatically. It should print the
complete follow-up chain so the operator can execute and inspect each step.

## Guardrails

- Do not write receipt events in tests or dry-runs.
- Do not record a send/return without `--execute`.
- Do not synthesize human labels or returned files.
- Do not mark report output ready.

