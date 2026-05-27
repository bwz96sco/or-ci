# Cost evidence operator packet design

## Boundary

Add:

`experiments/or-ci-paper-evidence-pack-2026-05-27/build_cost_evidence_operator_packet.py`

Generated artifacts:

- `cost-evidence-operator-packet-2026-05-27.json`
- `cost-evidence-operator-packet-2026-05-27.md`

Patch:

- `build_evidence_gate_smoke_report.py`

The builder reads finalization inputs and gates. It does not modify the operator
CSV and does not calculate final costs.

## Data Flow

Inputs:

- `cost-evidence-finalization-gate-2026-05-27.json`
- `cost-evidence-finalization-inputs-2026-05-27.csv`
- `paper-evidence-pack-readiness-2026-05-27.json`
- `human-evidence-collection-tracker-2026-05-27.json`

Output rows mirror the six finalization inputs. Each row carries a status,
required recorded fields, a guarded template, and the reason the paper row
remains blocked.

## Guardrails

Pending rows must not contain real recorded evidence fields. Recorded rows must
require value, unit, source_ref, recorded_by, and ISO-8601 recorded_at. The
operator packet may show templates with placeholders, but the finalization gate
remains authoritative for accepting real values.
