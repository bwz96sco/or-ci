# Design

## Boundary

This task adds operational glue in the notes repo only. It does not change
OR-CI verifier behavior or the canonical label-agreement analyzers.

## Data Flow

For each dataset:

1. Run or trust the existing intake gate check as the source of staged-label
   validity.
2. Read the intake readiness JSON.
3. Compare intake status with the dataset-specific ready status:
   - capstone: `ready_for_adjudication`.
   - Phase 2: `ready_for_phase2_50case_adjudication`.
   - NL4OPT: `ready_for_external_nl4opt_adjudication`.
4. Emit promotion readiness rows and summary.
5. Copy staged incoming Rater A/B CSVs into canonical target rater CSVs only
   when explicitly executed and the ready status is present.

## Safety Rules

- Default operation generates readiness artifacts only.
- `--check` validates readiness artifacts and does not copy labels.
- `--execute` requires `--dataset`.
- Copying is blocked unless the intake status is the exact ready status and
  issue count is zero.
- The generated Markdown must keep non-claims explicit.

## Generated Artifacts

Under `experiments/packs/or-ci-labeling-operations-2026-05-26/`:

- `label-promotion-readiness-2026-05-27.csv`
- `label-promotion-readiness-2026-05-27.json`
- `label-promotion-readiness-2026-05-27.md`

No canonical rater CSV files are modified in the current no-label state.
