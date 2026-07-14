# Cost evidence finalization gate design

## Boundary

Add a paper-pack gate under:

`experiments/packs/or-ci-paper-evidence-pack-2026-05-27/`

The gate reads the existing 50-case cost ledger:

`experiments/packs/or-ci-layered-verification-50case-2026-05-22/source-fidelity-50case-cost-throughput-ledger-2026-05-26.json`

It does not modify the 50-case ledger, human-label intake files, billing data,
or report claims.

## Artifacts

- `cost-evidence-finalization-inputs-2026-05-27.csv`
  Operator-editable source. Blank/pending rows are allowed and keep the gate
  blocked.
- `cost-evidence-finalization-gate-2026-05-27.json`
  Machine-readable readiness state.
- `cost-evidence-finalization-gate-2026-05-27.md`
  Human-readable report-output checklist.

## Input Rows

The CSV has fixed row ids:

- `billing_basis_policy`
- `price_card_or_billing_export`
- `latency_source_policy`
- `human_label_minutes`
- `human_adjudication_minutes`
- `accepted_artifact_denominator`

Allowed statuses:

- `pending_source`
- `pending_human_labels`
- `pending_adjudicated_labels`
- `recorded`

Rows marked `recorded` require value, unit, source reference, recorder, and
timestamp. Pending rows may stay blank and become blockers.

## Readiness Semantics

The gate is ready only when all six inputs are `recorded`. Until then:

- observed sessions/tokens/commands/solver calls may be reported as operational
  throughput evidence;
- dollar cost, latency, human-time, and cost-per-accepted-artifact claims remain
  forbidden.

## Integration

Paper readiness should use the finalization gate JSON as the cost row status
source and include the original 50-case ledger as supporting proof. Smoke should
run both `--check` and `--self-test` for the gate.
