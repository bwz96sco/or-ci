# Labeling Operations Dashboard Design

## Boundary

The dashboard lives in the notes repo as a cross-experiment operations artifact:

`experiments/or-ci-labeling-operations-2026-05-26/`

It reads existing labeling packets and label CSVs from:

- `or-ci-self-host-exploration-2026-05-25/`
- `or-ci-layered-verification-50case-2026-05-22/`
- `or-ci-external-sanity-nl4opt-2026-05-26/`

It does not edit those source label sheets and does not infer labels.

## Outputs

- `build_labeling_operations_dashboard.py`
- `labeling-dispatch-queue-2026-05-26.csv`
- `labeling-operations-summary-2026-05-26.json`
- `labeling-operations-summary-2026-05-26.md`

## Dispatch Model

Each dispatch row represents one required human action:

- `cold_rater`: capstone cold protocol check packets only.
- `rater_a`: primary rater label row.
- `rater_b`: independent overlap rater row, where required.
- `adjudicator`: final adjudication row after required rater labels exist.

Status is derived from label-sheet completeness. Current expected state is
pending for every row.

## Privacy Boundary

Rater-facing paths point only to blinded packet markdown files and blank label
sheets. Coordinator-only packet maps are referenced in the summary for the
coordinator, not as dispatch files for raters.

## Validation

The checker rebuilds the queue and summary from source artifacts and fails if
generated files are stale, packet files are missing, label CSVs have unexpected
packet sets, or agreement-summary files are missing.
