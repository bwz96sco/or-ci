# Implementation Plan

1. Add `build_evidence_gate_smoke_report.py` under the paper evidence-pack
   experiment directory.
2. Define the command registry with explicit paths, phase labels, and safe
   arguments.
3. Implement subprocess execution, output-tail capture, JSON/Markdown
   rendering, artifact writing, and `--check`.
4. Generate the initial JSON/Markdown smoke report.
5. Validate:
   - `uv run python .../build_evidence_gate_smoke_report.py --check`
   - representative existing gate checks/self-tests
   - `git diff --check` in code and notes repos
   - `uv run python ./.trellis/scripts/task.py validate 05-27-evidence-gate-smoke-runner`
   - `npx gitnexus detect-changes --repo or-ci --scope all`
6. Commit notes-vault artifacts, then archive and commit the Trellis task.
