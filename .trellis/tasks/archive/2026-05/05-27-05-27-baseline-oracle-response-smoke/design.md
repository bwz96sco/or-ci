# Baseline Oracle Response Smoke Design

## Boundary

This task exercises one row of the existing 52-row baseline-ablation run queue.
It may add one raw response artifact and update one row in the response
template. It does not change the prompt manifest or invent any model output.

## Selected Row

Default smoke row:

- condition: `direct_strong_llm`
- packet: `P001`
- input: `baseline-ablation-inputs-2026-05-26/direct_strong_llm/P001.md`
- output: `baseline-ablation-raw-responses-2026-05-26/direct_strong_llm/P001.json`

## Capture Rules

Oracle output must be preserved. If the returned text is a JSON object, store
it directly. If it is Markdown fenced JSON with no extra substantive answer,
extract the JSON object and preserve a sidecar failure/metadata note only if
needed. If it is not parseable JSON, do not fill a decision; record the failure.

## Validation Flow

After capture:

`baseline-ablation-response-template-2026-05-26.csv`
-> `build_baseline_ablation_run_package.py --check`
-> `build_baseline_ablation_results.py --check`

The queue should complete only the smoke row.
