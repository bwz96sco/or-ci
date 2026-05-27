# Verification

## Checks

- `PYTHONDONTWRITEBYTECODE=1 uv run python build_human_evidence_collection_tracker.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_human_labeling_handoff.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_parallel_labeling_distribution_packages.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_rater_packet_leakage_audit.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_label_promotion_readiness.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_paper_evidence_pack_readiness.py --self-test`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_paper_evidence_pack_readiness.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_next_stage_execution_board.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m py_compile build_paper_evidence_pack_readiness.py build_next_stage_execution_board.py`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_mutation_seed_review_operator_queue.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_mutation_seed_review_intake.py --check`
- `jq` assertions over board/readiness JSON confirming the tracker is sourced,
  cold check remains primary, tracker completed items are zero, and report-ready
  is false.
- `git diff --check`

## Evidence State

- Execution board source artifacts now include
  `human-evidence-collection-tracker-2026-05-27.json`.
- Human labeling handoff lists the tracker CSV/JSON/Markdown as the compact
  operator control surface.
- Paper evidence-pack readiness requires the tracker JSON/Markdown and snapshots
  tracker status, primary next action, ready parallel tracks, and completed
  item count.
- Missing evidence states are unchanged: cold check `0/5`, capstone blocked,
  Phase 2 and NL4OPT labels pending, mutation seeds unaccepted, and paper
  report-ready false.
