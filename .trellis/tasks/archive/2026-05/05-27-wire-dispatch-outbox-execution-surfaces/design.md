# Wire dispatch outbox design

## Boundary

Patch notes-side deterministic builders:

- `experiments/packs/or-ci-labeling-operations-2026-05-26/build_human_evidence_collection_tracker.py`
- `experiments/packs/or-ci-paper-evidence-pack-2026-05-27/build_next_stage_execution_board.py`

Generated artifacts will be refreshed by their existing builders.

## Data Flow

`build_human_dispatch_outbox_preflight.py` remains the source of truth for
package/checksum/sendability state.

The human tracker should read the outbox summary and add:

- global outbox status/counts;
- per-track preflight status map;
- Markdown pre-send guard bullets.

The execution board should read both the tracker and the outbox summary. It
should add outbox status/counts to the board summary and include the outbox
artifact in proof/source references for dispatch-facing rows.

## Guardrails

The wiring must not mutate:

- receipt event CSV;
- intake CSVs;
- canonical agreement inputs;
- mutation seed-review inputs;
- paper readiness decisions.

All generated text must keep `report_ready=false` in the current state.
