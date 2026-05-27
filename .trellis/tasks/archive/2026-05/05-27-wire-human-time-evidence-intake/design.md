# Wire human time evidence intake design

## Boundary

This task modifies notes-vault evidence builders under
`/Users/zhangbowen/Projects/OR/note/OR-research`. It does not modify the OR-CI
verifier package and does not create empirical evidence.

## Data flow

Operator-editable event log:

`human-time-evidence-events-2026-05-27.csv`

Generated readiness artifacts:

- `human-time-evidence-readiness-2026-05-27.json`
- `human-time-evidence-readiness-2026-05-27.csv`
- `human-time-evidence-readiness-2026-05-27.md`

Consumers:

- `build_cost_evidence_operator_packet.py` reads the readiness JSON and points
  human-time rows at it.
- `build_paper_evidence_pack_readiness.py` validates the readiness source and
  includes it in source artifacts.
- `build_evidence_gate_smoke_report.py` runs the readiness check and self-test.

## Contracts

The event CSV is append-only and empty by default. A recorded event must include
real values for event ID, wave/dataset, cost evidence category, work kind,
participant role, minutes, source reference, recorder, and timestamp. Pending
state is represented by zero event rows, not placeholder rows.

The readiness builder summarizes only recorded event rows. It may report zero
recorded minutes, but that is explicitly a pending-evidence state, not a proof
that human work took zero minutes.

## Compatibility

The existing final-cost input CSV remains authoritative for final cost values.
The new human-time readiness artifact is a provenance source and validator, not
an automatic writer into final cost rows.

## Risks

The main risk is accidentally turning an empty log into a reportable zero. The
readiness JSON therefore carries explicit `evidence_recorded=false` per category
until at least one valid event exists.
