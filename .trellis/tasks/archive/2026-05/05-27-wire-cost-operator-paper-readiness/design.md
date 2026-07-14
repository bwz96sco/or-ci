# Cost operator readiness wiring design

## Boundary

Patch:

- `experiments/packs/or-ci-paper-evidence-pack-2026-05-27/build_paper_evidence_pack_readiness.py`

Regenerate:

- `paper-evidence-pack-readiness-2026-05-27.*`
- `paper-evidence-pack-draft-2026-05-27.*`
- smoke report artifacts

## Data Flow

The cost finalization gate remains authoritative for final-cost readiness. The
cost operator packet is an auxiliary proof/action artifact. Readiness should
expose both:

- finalization gate: current status and blockers;
- operator packet: source for how to collect missing final-cost inputs.

## Guardrails

The current `cost_throughput_table` status must remain
`blocked_pending_cost_evidence_inputs`, and `report_ready` must remain false.
