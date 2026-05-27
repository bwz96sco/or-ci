# Verification

## Checks

- `PYTHONDONTWRITEBYTECODE=1 uv run python build_human_evidence_collection_tracker.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m py_compile build_human_evidence_collection_tracker.py`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_human_labeling_handoff.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_parallel_labeling_distribution_packages.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_rater_packet_leakage_audit.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_label_promotion_readiness.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_next_stage_execution_board.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_paper_evidence_pack_readiness.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_mutation_seed_review_operator_queue.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_mutation_seed_review_intake.py --check`
- `jq` assertions over `human-evidence-collection-tracker-2026-05-27.json`
  confirming cold check is primary at `0/5`, Phase 2 and NL4OPT are
  parallel-ready, capstone is blocked, mutation seed review remains pending,
  and `paper_report_ready=false`.

## Evidence State

- The generated tracker has five rows: cold protocol check, capstone labels,
  Phase 2 labels, NL4OPT labels, and mutation seed review.
- It records the cold check as the primary next action and keeps the capstone
  distribution blocked behind the cold protocol gate.
- It records 0 completed human labels, 0 accepted mutation seeds, 0 run-eligible
  mutation rows, 0 label-promotion-ready datasets, and paper report-ready false.
