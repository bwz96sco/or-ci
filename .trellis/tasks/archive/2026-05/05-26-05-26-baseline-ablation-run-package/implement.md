# Implementation Plan

1. Read the baseline prompt manifest, response template, run ledger, and
   existing baseline validators.
2. Add `build_baseline_ablation_run_package.py`.
3. Generate the run queue CSV, JSON summary, and Markdown status note.
4. Update the baseline runbook and roadmap/integration notes to reference the
   run queue.
5. Run:
   - `uv run python build_baseline_ablation_inputs.py --check`
   - `uv run python build_baseline_ablation_run_package.py --check`
   - `uv run python build_baseline_ablation_results.py --check`
   - `uv run python build_baseline_comparison.py --check`
   - `uv run pytest`
6. Commit notes changes, archive the Trellis task, and leave the overall
   research goal active.
