# Source Fidelity Labeling Calibration Checklist

## Setup

- [x] Read Trellis before-dev context.
- [x] Confirm capstone JSON, pilot artifact root, and experiment directory
  exist.
- [x] Confirm `or-ci`, `or_llm_agent`, and `OR-research` worktrees are clean.

## Implementation

- [x] Add `build_source_fidelity_adjudication.py` in the experiment directory.
- [x] Generate adjudication protocol Markdown.
- [x] Generate adjudication sheet CSV with 13 rows.
- [x] Generate calibration JSON and Markdown with pending-label status.
- [x] Update experiment README to cite the new artifacts.

## Verification

- [x] Run `uv run python build_source_fidelity_adjudication.py --check` in the
  experiment directory.
- [x] Verify calibration JSON parses.
- [x] Verify generated files exist and sheet has 13 unique rows.
- [x] Run `git diff --check` in OR research and OR-CI repos.
- [x] Review git status across OR-CI, OR-LLM-Agent, and OR research repos.

## Spec Update Judgment

- [x] No `.trellis/spec/` update is needed. This task added experiment-local
  report-building artifacts and did not change OR-CI verifier contracts,
  command signatures, package behavior, or reusable coding conventions.
