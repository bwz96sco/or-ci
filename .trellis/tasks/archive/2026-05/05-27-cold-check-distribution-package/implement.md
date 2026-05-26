# Implementation Plan

1. Add `build_cold_protocol_distribution_package.py`.
2. Read the safe bundle directory and generate deterministic ZIP bytes.
3. Write ZIP, JSON, and Markdown outputs.
4. Implement `--check` stale validation.
5. Update `build_human_labeling_handoff.py` to include distribution package
   pointers.
6. Regenerate the distribution package and human handoff.
7. Validate:
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_cold_protocol_distribution_package.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_cold_protocol_rater_bundle.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_human_labeling_handoff.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_rater_packet_leakage_audit.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_paper_evidence_pack_readiness.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_next_stage_execution_board.py --check`
   - whitespace checks.
