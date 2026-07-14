# Implementation Plan

1. [x] Confirm `llm_judge_no_rubric/P001` is pending in intake/capture/operator
   queues.
2. [x] Dry-run the Oracle prompt bundle.
3. [x] Run Oracle browser mode with Pro + extended thinking-time controls and save
   attempt output.
4. [x] Inspect session evidence and parse JSON.
5. [x] If valid:
   - write staged JSON with frozen metadata;
   - run response-intake check;
   - promote the row with `build_baseline_response_intake.py --promote`;
   - regenerate/check intake, capture, results, operator queue, paper readiness,
     and board artifacts.
6. [x] If invalid:
   - write a failure note;
   - ensure no staged/canonical response exists for this row.
   Not applicable: the response was valid and promoted.
7. [x] Run final validation:
   - `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-self-host-exploration-2026-05-25/build_baseline_response_intake.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-self-host-exploration-2026-05-25/build_baseline_response_capture.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-self-host-exploration-2026-05-25/build_baseline_ablation_results.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-self-host-exploration-2026-05-25/build_baseline_response_operator_queue.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-paper-evidence-pack-2026-05-27/build_paper_evidence_pack_readiness.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-paper-evidence-pack-2026-05-27/build_next_stage_execution_board.py --check`
   - `uv run pytest`
   - `git diff --check`
   - `git -C /Users/zhangbowen/Projects/OR/note/OR-research diff --check`
   - `npx gitnexus detect-changes --repo or-ci --scope all`
8. [x] Commit notes evidence and archive the Trellis task.
