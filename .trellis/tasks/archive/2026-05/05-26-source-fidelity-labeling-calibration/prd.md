# Source fidelity labeling calibration

## Goal

Create the independent source-fidelity adjudication protocol, 13-case labeling
sheet, and calibration report scaffold for the `source_fidelity_v1` capstone
without changing OR-CI verifier code.

## Target Inputs

- Capstone:
  `/Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/or-ci-self-host-exploration-2026-05-25/source-fidelity-rubric-capstone-2026-05-26.json`
- Pilot artifact root:
  `/Users/zhangbowen/Projects/OR/code/or-ci/artifacts/pilot/or-llm-agent-full-bwor-2026-05-25`
- Experiment directory:
  `/Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/or-ci-self-host-exploration-2026-05-25`

## Requirements

- Reuse the existing OR research adjudication vocabulary:
  `supported`, `needs_human`, `unsupported`, `accepted`, `rejected`,
  `not_applicable`, `not_needed`, `harmless_equivalent`, `material`,
  `unresolved`, `blocked`.
- Scope the first labeling kit to the 13 capstone cases:
  - Baseline: `BWOR-001`, `BWOR-016`, `BWOR-020`, `BWOR-027`, `BWOR-051`,
    `BWOR-061`, `BWOR-067`, `BWOR-071`, `BWOR-082`.
  - Clarified: `BWOR-014/attempt-1`, `BWOR-015/attempt-2`,
    `BWOR-027/attempt-1`, `BWOR-046/attempt-1`.
- Generate a CSV adjudication sheet with one row per case, preserving source
  paths, artifact paths, agent capability/fidelity fields, and blank human
  fields for later adjudication.
- Generate a protocol Markdown file that explains labels, decision rules,
  reason categories, and how to fill the sheet.
- Generate calibration JSON/Markdown that reports `pending_labels` when human
  labels are blank and computes agreement metrics when labels are filled.
- Add or update a small local helper script for deterministic regeneration and
  validation.
- Update the experiment README to link the new protocol, sheet, and calibration
  scaffold.

## Acceptance Criteria

- [ ] Experiment directory contains:
  - `source-fidelity-adjudication-protocol-2026-05-26.md`
  - `source-fidelity-adjudication-sheet-2026-05-26.csv`
  - `source-fidelity-calibration-2026-05-26.json`
  - `source-fidelity-calibration-2026-05-26.md`
  - `build_source_fidelity_adjudication.py`
- [ ] The adjudication sheet has exactly 13 unique rows and required columns
  for agent evidence plus human labels.
- [ ] The calibration report explicitly says human labels are pending when the
  sheet is blank.
- [ ] All referenced case artifact paths exist.
- [ ] README points to the new labeling and calibration artifacts.
- [ ] `uv run python build_source_fidelity_adjudication.py --check` passes in
  the experiment directory.
- [ ] The generated calibration JSON parses with `uv run python -m json.tool`.

## Out Of Scope

- Do not invent or fill human/expert labels.
- Do not expand to the full 50-case pilot in this task.
- Do not change OR-CI verifier code.
- Do not change OR-LLM-Agent product code unless reading existing artifacts is
  impossible.
