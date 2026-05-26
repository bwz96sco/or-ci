# Baseline P006 judge captures

## Goal

Capture, stage, promote, and validate the P006 Extended Pro baseline judge responses for no-rubric, rubric, and evidence-checklist conditions without touching direct_strong_llm rows.

## Confirmed Facts

- The next-stage roadmap and execution board keep human labels as the critical path, but baseline response capture is a parallel evidence-collection track.
- The baseline operator queue currently has 52 rows, 15 captured/recorded rows, 37 remaining submissions, and 0 issues.
- The completed baseline captures cover P001-P005 for `llm_judge_no_rubric`, `llm_judge_rubric`, and `llm_judge_evidence_checklist`.
- `direct_strong_llm` remains 0/13 and is intentionally excluded from this judge-capture slice because the direct-row policy is separate.
- No staged, raw, or failed-attempt P006 files are currently present for the targeted judge rows.
- Captured responses are bookkeeping evidence only. They must not be used to claim baseline performance, FAR reduction, source-fidelity accuracy, or paper branch readiness before the remaining rows and adjudicated human labels exist.

## Requirements

- Submit the P006 manual bundles for exactly these baseline conditions:
  - `llm_judge_no_rubric`
  - `llm_judge_rubric`
  - `llm_judge_evidence_checklist`
- Use Oracle browser mode against ChatGPT Extended Pro with the frozen baseline metadata:
  - `model_or_tool`: `oracle-cli browser ChatGPT Extended Pro`
  - `model_version`: `gpt-5.5-pro thinking-heavy via Extended Pro`
- Save only valid JSON objects to the staged response-intake paths.
- Promote each valid staged row explicitly through `build_baseline_response_intake.py --promote --baseline-condition <condition> --packet-id P006`.
- Regenerate and check the baseline response intake, capture, results summary, operator queue, paper evidence readiness, and next-stage execution board.
- Keep the existing review-plan notes and current-source documents consistent with the new 18/52 baseline count.
- Do not create, stage, promote, or infer any `direct_strong_llm` response.
- Do not infer a response from failed Oracle attempts, transcript prose, Markdown fences, Instant, ordinary Pro, or any non-Extended-Pro metadata.

## Acceptance Criteria

- [x] Three P006 judge staged JSON files exist and pass intake validation.
- [x] Three P006 judge rows are promoted into canonical raw response files and response-template records.
- [x] Baseline counts advance from 15/52 to 18/52 with 34 pending rows and 0 validation issues.
- [x] Per-condition captured counts become: `direct_strong_llm` 0/13, each judge condition 6/13.
- [x] `build_baseline_response_intake.py --check`, `build_baseline_response_capture.py --check`, `build_baseline_ablation_results.py --check`, and `build_baseline_response_operator_queue.py --check` pass.
- [x] `build_paper_evidence_pack_readiness.py --check` and `build_next_stage_execution_board.py --check` pass while keeping `report_ready=false`.
- [x] `uv run pytest`, `git diff --check`, notes `git diff --check`, and GitNexus change detection pass.
- [x] Task artifacts record the execution and are archived after validation.

## Notes

- Existing plan-refresh edits in the notes repo are retained and should be committed with the notes-side evidence update unless a separate notes commit is created first.
