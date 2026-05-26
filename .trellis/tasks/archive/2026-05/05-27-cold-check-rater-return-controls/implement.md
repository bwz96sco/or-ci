# Implementation Plan

1. Add constants for `RETURN-CHECKLIST.md` and `bundle-checksums.csv`.
2. Build checklist Markdown from the existing summary.
3. Build checksum CSV after the main expected file map is assembled.
4. Add checksum/checklist entries to `bundle-summary.json`.
5. Regenerate the cold protocol rater bundle.
6. Validate:
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_cold_protocol_rater_bundle.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_cold_protocol_intake.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_human_labeling_handoff.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_rater_packet_leakage_audit.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_paper_evidence_pack_readiness.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_next_stage_execution_board.py --check`
   - diff whitespace checks.
