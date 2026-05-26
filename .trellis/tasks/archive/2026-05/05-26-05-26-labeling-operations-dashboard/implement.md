# Implementation Plan

1. Inspect per-track rater sheets, packet indexes, and label-agreement
   summaries.
2. Add the cross-experiment dashboard builder script.
3. Generate dispatch queue, machine summary, and Markdown summary.
4. Update roadmap/integration notes to point human labeling work at the new
   dashboard.
5. Run:
   - `uv run python build_labeling_operations_dashboard.py --check`
   - capstone label agreement check
   - 50-case label agreement check
   - NL4OPT label agreement check
   - `uv run pytest`
6. Commit notes changes, archive the Trellis task, and keep the overall
   research goal active.
