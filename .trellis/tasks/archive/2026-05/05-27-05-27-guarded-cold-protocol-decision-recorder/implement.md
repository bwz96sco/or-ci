# Implementation Plan

1. Add `record_cold_protocol_review_decision.py` in the labeling operations
   experiment directory.
2. Reuse constants and validation helpers from `build_cold_protocol_review_gate.py`.
3. Implement `--check`, dry-run record, `--execute`, and `--self-test`.
4. Wire the recorder check/self-test into
   `build_evidence_gate_smoke_report.py`.
5. Update roadmap/sync notes and smoke command count.
6. Run validation:
   - recorder `--check` and `--self-test`;
   - a dry-run blocked-intake rejection, proving no decision row is written;
   - cold review/capstone/receipt/paper/board checks;
   - smoke check;
   - `uv run pytest`;
   - Trellis task validate;
   - GitNexus detect changes before code-repo commit.
