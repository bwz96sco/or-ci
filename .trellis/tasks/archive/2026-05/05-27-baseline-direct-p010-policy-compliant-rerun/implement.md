# Implementation Plan

1. Update the notes policy with a P010-only infrastructure-failure retry
   addendum.
2. Run Oracle browser mode for P010 with the frozen Extended Pro settings and
   JSON-safe wrapper prompt.
3. Inspect Oracle session metadata and final output.
4. If the attempt is valid Extended Pro JSON, stage `P010.json`, run the intake
   check, promote the row, and regenerate downstream artifacts.
5. If the attempt is invalid, keep it only as failed attempt evidence and
   regenerate readiness artifacts if their operator action text changes.
6. Update roadmap/reconciliation/sync notes to match the final state.
7. Run verification:
   - `uv run python build_baseline_response_intake.py --check`
   - `uv run python build_baseline_response_capture.py --check`
   - `uv run python build_baseline_ablation_results.py --check`
   - `uv run python build_baseline_response_operator_queue.py --check`
   - `uv run python build_baseline_comparison.py --check`
   - `uv run python build_paper_evidence_pack_readiness.py --check`
   - `uv run python build_next_stage_execution_board.py --check`
   - `uv run pytest`
   - `git diff --check` in code and notes repos
   - `npx gitnexus detect-changes --repo or-ci --scope all`

Rollback point: if the extra P010 attempt fails, do not stage it. The policy
addendum and failed attempt transcript remain useful evidence, while P010 stays
pending.
