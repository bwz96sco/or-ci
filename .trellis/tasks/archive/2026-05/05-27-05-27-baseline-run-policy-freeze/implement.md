# Implementation Plan

1. Fill the run-ledger policy fields for the four external baseline conditions.
2. Add a baseline model-run policy note.
3. Regenerate the baseline-ablation run queue.
4. Update the roadmap/integration notes to point at the ready queue.
5. Run:
   - `uv run python build_baseline_ablation_inputs.py --check`
   - `uv run python build_baseline_ablation_run_package.py --check`
   - `uv run python build_baseline_ablation_results.py --check`
   - `uv run python build_baseline_comparison.py --check`
   - `uv run pytest`
6. Commit notes changes, archive this Trellis task, and keep the overall
   research goal active.
