# Source Fidelity Evidence Capstone Checklist

## Setup

- [x] Read Trellis before-dev context.
- [x] Confirm target batch root and experiment directory exist.
- [x] Confirm OR-CI and OR-LLM-Agent worktrees are clean before durable edits.

## Evidence Run

- [x] Run baseline `review-fidelity-batch --mode agent` for selected IDs.
- [x] Run clarified `review-fidelity --mode agent` for selected clarified artifacts.
- [x] Inspect generated rubric JSON/Markdown outputs.
- [x] Build report-facing capstone JSON and Markdown in the experiment directory.
- [x] Update README conclusion, fidelity risk, next tasks, and final state.

## Verification

- [x] Run `uv run pytest tests` in `../or_llm_agent`.
- [x] Verify generated capstone JSON parses.
- [x] Verify README/capstone links point to existing files.
- [x] Review git status across OR-CI, OR-LLM-Agent, and note repo.

## Spec Update Judgment

- No `.trellis/spec/` update is needed. This task generated research-report
  evidence artifacts and did not change OR-CI command signatures, data
  contracts, verifier behavior, package layout, or reusable coding conventions.
