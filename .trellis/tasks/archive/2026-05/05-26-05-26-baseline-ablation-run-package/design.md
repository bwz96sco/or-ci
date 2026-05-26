# Baseline Ablation Run Package Design

## Boundary

This task edits research-note experiment artifacts only. It does not modify the
OR-CI verifier package and does not call model providers.

## Inputs

- `baseline-ablation-prompt-manifest-2026-05-26.csv`
- `baseline-ablation-response-template-2026-05-26.csv`
- `baseline-run-ledger-template-2026-05-26.csv`
- `baseline-ablation-runbook-2026-05-26.md`

## Outputs

- `build_baseline_ablation_run_package.py`
- `baseline-ablation-run-queue-2026-05-26.csv`
- `baseline-ablation-run-queue-2026-05-26.json`
- `baseline-ablation-run-queue-summary-2026-05-26.md`

## Data Flow

Each prompt-manifest row becomes one run-queue row. The queue records:

- condition and packet id;
- input prompt path;
- expected raw response path;
- expected response kind;
- ledger model/tool/version/settings;
- readiness/completion status;
- response-template linkage.

The raw response path is deterministic:

`baseline-ablation-raw-responses-2026-05-26/<condition>/<packet_id>.json`

The queue is current-state bookkeeping. It is not a model runner and does not
create placeholder response JSON files.

## Status Rules

- `blocked_pending_model_policy`: ledger model/tool, model version, temperature,
  or retry policy is missing for an external model condition.
- `ready_for_external_model_run`: model policy exists, prompt exists, and no
  response is recorded.
- `completed_response_recorded`: response template points to existing raw JSON
  and decision metadata.

Current expected status is blocked/pending, not complete.

## Validation

The checker rebuilds the queue from source manifests and fails if generated
queue/summary files are stale. It verifies unique response paths, existing
input files, condition coverage, response-template consistency, and ledger
policy readiness.
