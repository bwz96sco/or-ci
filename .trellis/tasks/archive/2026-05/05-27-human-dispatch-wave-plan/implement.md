# Implementation Plan

1. Add `build_human_dispatch_wave_plan.py` in the labeling-operations
   experiment directory.
2. Implement source loading, path validation, wave classification, JSON
   summary, Markdown rendering, and `--check`.
3. Generate `human-dispatch-wave-plan-2026-05-27.{json,md}`.
4. Add the new wave-plan check to the evidence gate smoke runner registry.
5. Regenerate/check the smoke report.
6. Validate:
   - `build_human_dispatch_wave_plan.py --check`
   - `build_evidence_gate_smoke_report.py --check`
   - relevant tracker/dashboard/board/readiness checks
   - `py_compile`
   - `git diff --check` in both repos
   - `task.py validate`
   - `npx gitnexus detect-changes --repo or-ci --scope all`
7. Commit notes-vault artifacts and archive the Trellis task.
