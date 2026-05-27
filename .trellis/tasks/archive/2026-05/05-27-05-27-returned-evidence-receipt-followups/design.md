# Returned evidence receipt follow-up commands design

## Boundary

The change stays inside the notes-vault staging helper:

`experiments/or-ci-labeling-operations-2026-05-26/stage_returned_human_evidence.py`

It does not modify intake validators, receipt-event recorder semantics, or
paper-readiness logic. The existing smoke report already runs the staging
helper check and self-test, so smoke only needs regeneration if generated
reports drift.

## Data Shape

Add optional receipt metadata to each `StagingTarget`:

- `receipt_wave_id`: dispatch wave id when a staged file maps to a whole
  returned dispatch artifact.
- `receipt_note`: default receipt note for the returned-event preview.
- `receipt_requires_complete_wave`: explanation for split-label targets where
  one staged CSV is not enough to record the dispatch-wave return.

Single-file targets receive a concrete wave id:

- `cold_protocol_check` -> `wave_01_cold_protocol_check`
- `mutation_seed_review` -> `wave_06_mutation_seed_review`

Split-label targets get explanatory guidance and no command because their
dispatch-wave receipt represents the returned package/file set, not one
individual rater sheet.

## Output Contract

After the existing follow-up validation commands, print a `receipt bookkeeping`
section:

- single-file target: exact dry-run recorder command with `<ISO-8601 returned
  timestamp>` placeholder and the computed source SHA-256;
- split-label target: no-command note explaining when to record the wave-level
  return receipt.

The command intentionally omits `--execute`.

## Safety

The staging helper still writes only with `--execute`, and the receipt command
is text output only. The receipt recorder itself continues to reject return
events until a send event has actually been recorded.
