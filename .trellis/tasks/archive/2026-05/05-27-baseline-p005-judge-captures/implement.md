# Implementation Plan

1. [x] Confirm the three target judge rows are pending and P001-P004 judge rows are
   already captured.
2. [x] For each target row:
   - run Oracle browser mode with Pro + extended thinking-time controls;
   - parse the saved answer as JSON;
   - if valid, stage and promote through `build_baseline_response_intake.py`;
   - if invalid, leave staged/canonical paths absent and keep the attempt
     output as failure evidence.
3. [x] Regenerate/check:
   - `build_baseline_response_intake.py`
   - `build_baseline_response_capture.py`
   - `build_baseline_ablation_results.py`
   - `build_baseline_response_operator_queue.py`
   - `build_paper_evidence_pack_readiness.py`
   - `build_next_stage_execution_board.py`
4. [x] Run final validation:
   - all commands above with `--check`
   - `uv run pytest`
   - `git diff --check`
   - `git -C /Users/zhangbowen/Projects/OR/note/OR-research diff --check`
   - `npx gitnexus detect-changes --repo or-ci --scope all`
5. [ ] Commit notes evidence and archive the Trellis task.

## Execution Log

- Promoted `llm_judge_no_rubric/P005` from Oracle session `p005-judge-no`.
- Promoted `llm_judge_rubric/P005` from Oracle session `p005-judge-rubric`.
- Promoted `llm_judge_evidence_checklist/P005` from Oracle session
  `p005-judge-evidence`.
- All three rows returned valid JSON and accepted the packet.
- Oracle metadata requested `gpt-5.5-pro` with `thinkingTime: extended`; model
  picker evidence resolved as `Extended Pro` for the rubric and
  evidence-checklist rows and `Pro` with extended thinking-time controls for
  the no-rubric row.
- Downstream artifacts now report 15 completed baseline responses and 37 pending
  baseline responses.
- Verification passed: intake/capture/results/operator/readiness/board checks,
  `uv run pytest`, both `git diff --check` commands, and
  `npx gitnexus detect-changes --repo or-ci --scope all`.
