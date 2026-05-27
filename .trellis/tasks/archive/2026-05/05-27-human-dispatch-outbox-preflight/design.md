# Human dispatch outbox preflight design

## Boundary

Add:

`experiments/or-ci-labeling-operations-2026-05-26/build_human_dispatch_outbox_preflight.py`

Generated artifacts:

- `human-dispatch-outbox-preflight-2026-05-27.json`
- `human-dispatch-outbox-preflight-2026-05-27.csv`
- `human-dispatch-outbox-preflight-2026-05-27.md`

Patch:

- `experiments/or-ci-paper-evidence-pack-2026-05-27/build_evidence_gate_smoke_report.py`

The builder reads existing generated and operator-editable artifacts. It does
not write to receipt events, intake CSVs, canonical labels, mutation review
files, or paper readiness inputs.

## Inputs

- Human dispatch wave plan JSON.
- Human dispatch receipt ledger JSON and receipt events CSV.
- Rater-packet leakage audit JSON.
- Cold protocol distribution summary JSON and cold intake readiness JSON.
- Phase 2 distribution summary JSON and intake readiness JSON.
- NL4OPT distribution summary JSON and intake readiness JSON.
- Mutation seed-review operator queue JSON and seed-review intake/readiness
  JSON when available through existing queue fields.

## Row Semantics

Each wave emits:

- track, wave id, send state, receipt status, package path, target path;
- package checks for existence, SHA, and byte size when applicable;
- target readiness check;
- leakage check;
- preflight status:
  - `safe_to_send`;
  - `safe_to_assign_review`;
  - `blocked_by_prior_gate`;
  - `blocked_by_preflight_failure`;
  - `already_sent_or_returned`;
- issues and next operator action.

ZIP rows must match the SHA and byte count advertised by the existing wave
plan. Directory review rows must prove the directory and review sheet exist,
but must not invent a SHA.

## Current Expected State

Current data should produce:

- safe rows for cold protocol check, Phase 2, and NL4OPT;
- assignable row for mutation seed review;
- blocked rows for cold protocol review, capstone labels, and paper report
  output;
- no report-ready transition and no empirical claim.

## Smoke

The paper evidence-gate smoke report should run the preflight `--check` and
`--self-test` so stale or unsafe dispatch metadata blocks the overall evidence
gate.
