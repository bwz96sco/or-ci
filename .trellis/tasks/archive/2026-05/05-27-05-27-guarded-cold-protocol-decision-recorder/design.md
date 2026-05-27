# Design

## Scope

The task adds one operator recorder beside the existing cold-protocol review
gate. It writes only the operator-editable protocol-review decision CSV and
only when `--execute` is supplied. It does not modify generated readiness
files, cold-label intake files, capstone bundles, or receipt-event files.

## Inputs

- `cold-protocol-intake-readiness-2026-05-27.json`
- `cold-protocol-review-2026-05-27/protocol-review-decision.csv`
- `build_cold_protocol_review_gate.py` for shared decision field names,
  allowed status semantics, and validation.

## Behavior

The recorder has three operating modes:

- `--check`: validate the current decision CSV against the current cold intake
  gate and print the current decision state.
- dry-run record: validate a proposed decision and print the exact CSV row
  that would be written; do not write files.
- `--execute`: write the exact validated row to the decision CSV.

The recorder refuses:

- missing or placeholder decision metadata;
- unknown decisions;
- `revise_protocol` without `affected_labels_to_restart`;
- any nonblank decision while cold intake is not `ready_for_protocol_review`;
- overwriting a nonblank existing decision.

## Validation

`--self-test` uses in-memory synthetic cold-intake states and decision rows to
cover:

- valid `accept_protocol` after ready cold intake;
- valid `keep_blocked` after ready cold intake;
- invalid `revise_protocol` without restart scope;
- invalid decision while cold intake is blocked;
- invalid overwrite of an existing decision.

## Smoke Integration

Add two safe command specs to `build_evidence_gate_smoke_report.py`:

- `cold_protocol_review_decision_recorder_check`;
- `cold_protocol_review_decision_recorder_self_test`.

Both are non-mutating.

## Rollback

Remove the recorder script, remove the two smoke command specs, regenerate the
smoke report, and remove any roadmap/sync note references added for the
recorder.
