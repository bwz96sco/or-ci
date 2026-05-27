# Implementation Plan

1. Add `stage_returned_human_evidence.py` in the labeling operations
   experiment directory.
2. Build the staging target registry from existing bundle/intake constants
   where practical.
3. Implement source/target validation, dry-run output, `--execute`, `--check`,
   and `--self-test`.
4. Wire check/self-test into `build_evidence_gate_smoke_report.py`.
5. Update roadmap/sync notes and smoke command count.
6. Run validation:
   - helper `--check` and `--self-test`;
   - rejected placeholder/missing-source dry-run with no target diff;
   - intake/receipt/paper/board checks;
   - smoke check;
   - `uv run pytest`;
   - Trellis task validate;
   - GitNexus detect changes before code-repo commit.
