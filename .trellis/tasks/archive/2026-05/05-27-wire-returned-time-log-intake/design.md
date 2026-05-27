# Design: Wire returned time-log intake

## Context

Rater bundles now include a bundle-local `human-time-log.csv`, but the
canonical cost/readiness gate reads
`human-time-evidence-events-2026-05-27.csv`. Without a guarded conversion path,
the coordinator would have to hand-edit the canonical event log after returned
time logs arrive.

## Approach

Add `stage_returned_human_time_log.py` beside the other labeling-operations
helpers. Its default mode is dry-run. It accepts:

- `--target`: one of the known labeling waves.
- `--source`: a returned `human-time-log.csv`.
- `--source-sha256`: optional checksum guard.
- `--recorded-by` and `--recorded-at`: operator provenance for the canonical
  event rows.
- `--execute`: append rows to the canonical event log after preview.

The helper validates returned time-log rows before mapping them to canonical
events. It derives:

- `event_id`: deterministic from target, participant role, participant id or
  anonymous slot, source digest prefix, and row index.
- `wave_id`: from target config.
- `cost_evidence_id`: `human_label_minutes` for returned rater logs.
- `source_ref`: relative source path plus SHA-256.

It does not try to infer adjudication time; that remains a future adjudicator
log path.

## Role Correction

The cold-protocol rater time log should use `second_rater`, not `cold_rater`,
because `second_rater` is already the canonical human-time readiness role.

## Non-Goals

- Do not copy label sheets.
- Do not record time events in checks or self-tests.
- Do not mark human-time readiness complete without a real returned source and
  `--execute`.
- Do not finalize cost inputs.
