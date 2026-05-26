# Implementation Plan

1. Read the active specs and existing bundle builder patterns.
2. Add a reusable safe rater-instruction generator for v2 labels.
3. Update each bundle builder to emit and check `RATER-INSTRUCTIONS.md`.
4. Regenerate the four safe rater bundles.
5. Refresh handoff/readiness artifacts that summarize bundle contents.
6. Run validation:
   - `uv run python build_cold_protocol_rater_bundle.py --check`
   - `uv run python build_capstone_rater_bundle.py --check`
   - `uv run python build_phase2_50case_rater_bundle.py --check`
   - `uv run python build_nl4opt_rater_bundle.py --check`
   - `uv run python build_rater_packet_leakage_audit.py --check`
   - `uv run python build_human_labeling_handoff.py --check`
   - `uv run python build_paper_evidence_pack_readiness.py --check`
   - `git diff --check`
7. Commit note-vault changes, archive the Trellis task, and commit the Trellis archive if applicable.
