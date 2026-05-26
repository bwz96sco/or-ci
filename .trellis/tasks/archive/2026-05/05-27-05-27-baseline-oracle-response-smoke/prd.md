# Capture baseline Oracle response smoke

## Goal

Run and record the first queued Oracle/Extended Pro baseline-ablation response
as a smoke test for the 52-row external model queue without fabricating model
output.

## Requirements

- Use the frozen policy in
  `baseline-model-run-policy-2026-05-27.md`.
- Select exactly one queued `ready_for_external_model_run` row for the smoke
  run, starting with `direct_strong_llm` / `P001` unless the queue state has
  changed.
- Submit the queued prompt through Oracle CLI browser mode with GPT-5.5 Pro /
  Extended Pro.
- Save only the actual assistant output returned by Oracle as the raw response
  artifact at the queue's `expected_raw_response_file` path.
- Update `baseline-ablation-response-template-2026-05-26.csv` only from the
  actual run metadata and parsed raw response.
- If Oracle/browser fails, record the failure in a note without fabricating a
  response JSON or response decision.
- Keep all remaining 51 queued rows ready/pending; do not mark them complete.

## Acceptance Criteria

- [x] One raw response JSON exists for the selected queue row, or a failure note
      records why no response could be captured.
- [x] If a raw response exists, the matching response-template row records
      `run_id`, `model_or_tool`, `model_version`, `response_file`, and
      `decision` from the actual output.
- [x] `build_baseline_ablation_run_package.py --check` passes after the smoke
      run or failure record.
- [x] `build_baseline_ablation_results.py --check` passes.
- [x] The run queue reports either 1 completed and 51 ready rows, or remains 52
      ready rows with a failure note and no fabricated response.
- [x] `uv run pytest` for OR-CI still passes.

## Out of Scope

- Running all 52 baseline prompts.
- Retrying for answer quality.
- Editing the prompt content after seeing model output.
- Claiming baseline metrics before human labels exist.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
