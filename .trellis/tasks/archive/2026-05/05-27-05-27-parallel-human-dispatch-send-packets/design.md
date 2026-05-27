# Design

## Scope

This task adds one notes-vault generator and wires its non-mutating checks into
the existing evidence-gate smoke report. It does not touch OR-CI verifier
runtime code and does not write receipt events, labels, seed decisions,
baseline responses, mutation outputs, or report-ready claims.

## Inputs

The generator reads the existing source-of-truth artifacts:

- `human-dispatch-wave-plan-2026-05-27.json`
- `human-dispatch-receipt-ledger-2026-05-27.json`
- `human-dispatch-receipt-events-2026-05-27.csv`
- `phase2-50case-rater-bundle-distribution-2026-05-27.json`
- `nl4opt-rater-bundle-distribution-2026-05-27.json`
- `mutation-seed-review-operator-queue-2026-05-27.json`
- `mutation-seed-review-bundle-2026-05-27/bundle-summary.json`

## Outputs

The generator writes:

- `parallel-human-dispatch-send-packets-2026-05-27.json`
- `parallel-human-dispatch-send-packets-2026-05-27.md`

The JSON is the structured operator packet. The Markdown is the copy-ready
coordinator surface for sending Phase 2, NL4OPT, and mutation seed-review
requests.

## Validation

The generator validates that the three included waves are in a ready state,
unsent in both the receipt ledger and receipt-events CSV, and backed by
existing packages or bundle files. ZIP packages are re-hashed and compared to
their distribution summaries. The mutation seed-review bundle is validated as
a directory bundle with the expected review file, manifest, packet count, and
pending-review queue state.

`--check` rebuilds the expected JSON/Markdown in memory and fails if generated
artifacts are stale. `--self-test` mutates in-memory copies to prove unsafe
states are rejected, including already-sent rows, blocked waves, missing
packages, and checksum mismatches.

## Smoke Integration

`build_evidence_gate_smoke_report.py` gets two new command specs:

- `parallel_human_dispatch_send_packets_check`
- `parallel_human_dispatch_send_packets_self_test`

Both use safe arguments only and run without recording sends or modifying
human-evidence state.

## Rollback

Remove the new generator and generated JSON/Markdown artifacts, then remove
the two smoke command specs and regenerate the smoke report.
