# Freeze baseline ablation run policy

## Goal

Freeze model/tool/version/temperature/retry policy for the baseline-ablation external model run queue without creating or inferring model responses.

## Requirements

- Freeze the external model policy for these four baseline-ablation conditions:
  - `direct_strong_llm`
  - `llm_judge_no_rubric`
  - `llm_judge_rubric`
  - `llm_judge_evidence_checklist`
- Use the user-specified Oracle CLI browser path with ChatGPT Extended Pro /
  GPT-5.5 Pro thinking-heavy semantics.
- Fill the required run-ledger policy fields: `model_or_tool`,
  `model_version`, `temperature`, `max_retries`, and `runner`.
- Regenerate the baseline-ablation run queue so the 52 queued rows become
  `ready_for_external_model_run`, not completed.
- Add a short policy note documenting how to run the queued prompts and what
  must not be inferred before raw response JSON and human labels exist.
- Update the roadmap without claiming any model responses, baseline decisions,
  source-fidelity accuracy, or FAR result.

## Acceptance Criteria

- [x] The four external model conditions in
      `baseline-run-ledger-template-2026-05-26.csv` have frozen non-empty
      model/tool, model version, temperature, retry, and runner policy fields.
- [x] `baseline-ablation-run-queue-2026-05-26.csv` reports 52 rows ready for
      external model runs and 0 completed responses.
- [x] A policy note records the Oracle CLI browser/Extended Pro/GPT-5.5
      thinking-heavy run policy and retry rule.
- [x] `build_baseline_ablation_run_package.py --check` passes.
- [x] Existing baseline input/result/comparison checks still pass.
- [x] `uv run pytest` for OR-CI still passes.
- [x] Roadmap status is updated without claiming baseline run completion.

## Out of Scope

- Calling Oracle or ChatGPT Pro for the 52 queued prompts.
- Creating raw response JSON files.
- Filling response decisions.
- Computing baseline metrics or FAR claims before adjudicated human labels.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
