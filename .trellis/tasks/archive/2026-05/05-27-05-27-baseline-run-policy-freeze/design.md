# Baseline Run Policy Freeze Design

## Boundary

This task updates notes artifacts under:

`experiments/or-ci-self-host-exploration-2026-05-25/`

It does not edit OR-CI verifier code and does not call an external model.

## Policy Contract

The four external baseline conditions share one frozen policy:

- Tool: Oracle CLI browser mode.
- Model surface: ChatGPT Extended Pro.
- Model/version label: GPT-5.5 Pro thinking-heavy via Extended Pro.
- Temperature: UI default, not user-configurable in browser mode.
- Retries: one infrastructure retry only; no retry for answer quality.

The queue builder treats these policy fields as enough to mark rows
`ready_for_external_model_run`. A row becomes complete only after a raw response
JSON exists and the response template records the run metadata and decision.

## Data Flow

`baseline-run-ledger-template-2026-05-26.csv`
-> `build_baseline_ablation_run_package.py`
-> `baseline-ablation-run-queue-2026-05-26.{csv,json,md}`

The policy note documents the browser/Oracle execution policy for humans or a
future automation slice that actually submits prompts.

## Non-Claims

Ready queue rows are not model results. They do not imply a baseline decision,
accuracy, source-fidelity agreement, or false-accept metric.
