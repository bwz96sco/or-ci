# Verification

## Checks

- `PYTHONDONTWRITEBYTECODE=1 uv run python build_next_stage_execution_board.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_paper_evidence_pack_readiness.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_human_labeling_handoff.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_parallel_labeling_distribution_packages.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_label_promotion_readiness.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m py_compile build_next_stage_execution_board.py`
- `git diff --check`

## Evidence State

- The board status remains `pending_external_evidence_collection`.
- The primary next action remains `complete_5_cold_check_labels`.
- Phase 2 remains 0/50 complete and points to its sendable ZIP, dispatch
  brief, distribution summary, and intake readiness gate.
- NL4OPT remains 0/20 complete and points to its sendable ZIP, dispatch brief,
  distribution summary, and intake readiness gate.
- Label promotion remains blocked with 0 ready datasets.
- Paper report readiness remains false.
