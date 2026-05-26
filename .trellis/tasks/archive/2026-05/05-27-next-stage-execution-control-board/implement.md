# Implementation Plan

1. Add `build_next_stage_execution_board.py` in the paper evidence-pack
   experiment directory.
2. Load the five source JSON files and validate expected high-level keys.
3. Build eight deterministic action rows from current gate snapshots.
4. Build a JSON summary with source artifacts, status counts, owner/action
   counts, primary next action, and non-claims.
5. Render Markdown with current situation, critical path, parallel tracks,
   verification commands, and forbidden claims.
6. Implement default generation and `--check` stale validation.
7. Generate CSV/JSON/Markdown artifacts.
8. Update roadmap, reconciliation, and review-sync notes to reference the new
   board.
9. Validate:
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_next_stage_execution_board.py`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_next_stage_execution_board.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_paper_evidence_pack_readiness.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_human_labeling_handoff.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_baseline_response_operator_queue.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_mutation_seed_review_operator_queue.py --check`
   - `git diff --check`
   - `git -C /Users/zhangbowen/Projects/OR/note/OR-research diff --check`
10. Run GitNexus detect-changes before archiving the Trellis task.
