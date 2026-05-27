# Verification

## Checks

- `PYTHONDONTWRITEBYTECODE=1 uv run python build_paper_evidence_pack_readiness.py --self-test`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_paper_evidence_pack_readiness.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_next_stage_execution_board.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_human_labeling_handoff.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_parallel_labeling_distribution_packages.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_rater_packet_leakage_audit.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_label_promotion_readiness.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m py_compile build_paper_evidence_pack_readiness.py build_next_stage_execution_board.py`
- `git diff --check`

## Evidence State

- Cold, capstone, Phase 2, and NL4OPT distribution summaries are validated
  against expected status, ZIP existence, and ZIP SHA-256.
- Paper-readiness rows cite distribution summaries, dispatch briefs, and intake
  gates for label-dependent report sections.
- Missing-label states remain unchanged: capstone, Phase 2, and NL4OPT are
  still pending human labels; the paper evidence pack remains
  `report_ready=false`.
