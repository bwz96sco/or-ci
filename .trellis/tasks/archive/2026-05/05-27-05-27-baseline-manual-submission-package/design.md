# Manual Baseline Submission Package Design

## Boundary

This task adds generated manual-submission artifacts under:

`experiments/or-ci-self-host-exploration-2026-05-25/`

It does not change OR-CI verifier code, model prompts, or response records.

## Outputs

- `build_baseline_manual_submission_package.py`
- `baseline-ablation-manual-submissions-2026-05-27/`
- `baseline-ablation-manual-submission-manifest-2026-05-27.csv`
- `baseline-ablation-manual-submission-manifest-2026-05-27.json`
- `baseline-ablation-manual-submission-summary-2026-05-27.md`

## Data Flow

`baseline-ablation-run-queue-2026-05-26.csv`
-> prompt files and output schema
-> manual submission bundles
-> manifest and summary

The package is a fallback for Oracle browser-cookie failures. It preserves the
same queue and expected raw-response paths, so responses can later be stored and
validated by the existing response-template and results scripts.

## Validation

The checker rebuilds expected bundle text from the queue and fails if any
generated bundle, manifest, or summary is stale. It also verifies that the raw
response files are not accidentally created by this task.
