# Build constructed fault pilot inventory scripts

## Goal

Build the first executable inventory layer for the constructed source-fidelity
fault benchmark. The scripts should turn the existing BWOR artifacts and prior
mutation scaffolds into a reproducible no-human-label pilot plan:

1. eligible seed inventory;
2. source-fidelity fault-family applicability matrix;
3. side-effect-free pilot mutation plan.

This task does not generate mutated artifacts, run solvers, run OR-CI, or call
LLM judges. It prepares the denominator and planning inputs for those later
research-experiment stages.

## Requirements

- Add deterministic Python build scripts under:
  `/Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10/`.
- Use only local artifact evidence:
  - existing 82-case OR-CI/BWOR artifact root;
  - prior mutation seed manifests, applicability matrices, and plan previews;
  - existing experiment contract and run matrix.
- Replace the old `human_accepted_seed` blocker with explicit no-human-label
  eligibility fields:
  - source statement exists;
  - generated ProblemSpec or equivalent structured artifact exists;
  - generated solver/submission artifact exists when available;
  - original solver result exists or is traceable;
  - OR-CI report/result exists when applicable;
  - BWOR/reference answer signal exists when used;
  - no unresolved source-fidelity rejection is known from local evidence.
- Preserve research caveats:
  - author spot checks are QA, not independent human-label evidence;
  - no human-calibrated source-fidelity accuracy claim;
  - no natural-distribution false-accept-rate claim;
  - no OR-CI `PASS` implies source-fidelity claim.
- Output stable CSV, JSON, and Markdown summaries for each build stage:
  - `seed_inventory.{csv,json,md}`;
  - `fault_family_applicability.{csv,json,md}`;
  - `pilot_mutation_plan.{csv,json,md}`.
- Every script must support `--check` to detect stale generated artifacts.
- The pilot mutation plan must be side-effect-free: it may name future mutant
  artifact paths and target fields, but it must not write mutated ProblemSpecs
  or solver outputs.
- Deterministic selection rule:
  - choose 3-5 eligible pilot seeds when possible;
  - cover as many of the five initial source-fidelity fault families as local
    evidence supports;
  - plan at least 10 seed-family rows if enough applicable combinations exist.
- Prefer stdlib (`argparse`, `csv`, `json`, `pathlib`) and do not add package
  dependencies.
- Do not edit OR-CI verifier internals for this task.

## Acceptance Criteria

- [ ] Trellis task artifacts (`prd.md`, `design.md`, `implement.md`) describe
      scope, constraints, validation, and non-goals.
- [ ] `build_seed_inventory.py` writes and checks
      `seed_inventory.{csv,json,md}` with reproducible eligibility accounting.
- [ ] `build_fault_family_applicability.py` writes and checks
      `fault_family_applicability.{csv,json,md}` for the five initial
      constructed source-fidelity fault families.
- [ ] `build_pilot_mutation_plan.py` writes and checks
      `pilot_mutation_plan.{csv,json,md}` without generating mutants.
- [ ] Generated JSON summaries include denominator caveats and non-claims.
- [ ] Generated Markdown summaries are readable as report inputs.
- [ ] `uv run python <script> --check` passes for all new scripts.
- [ ] The research-experiment pack validator is run; missing future-stage
      execution/result files are reported as expected, not hidden.
- [ ] Git diff is reviewed so unrelated `.mcp.json` changes remain untouched.

## Notes

- This task implements the "sanity_seed_inventory" and
  "sanity_fault_family_applicability" rows in `run_matrix.yaml`, plus the
  side-effect-free planning part of "pilot_mutant_generation_3x5".
- The old mutation scaffolds remain useful evidence sources, but this task must
  not inherit their human-label gate as a blocker.
