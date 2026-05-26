# Implementation Plan

1. Add the manual submission package builder.
2. Generate 52 bundles and manifest/summary artifacts.
3. Update roadmap and review integration notes.
4. Run:
   - `uv run python build_baseline_manual_submission_package.py --check`
   - `uv run python build_baseline_ablation_run_package.py --check`
   - `uv run python build_baseline_ablation_results.py --check`
   - `uv run pytest`
5. Commit notes changes, archive the Trellis task, and keep the overall
   research goal active.
