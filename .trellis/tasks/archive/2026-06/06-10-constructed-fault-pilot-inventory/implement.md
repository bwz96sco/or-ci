# Implementation Plan

## 1. Planning Gate

- Validate Trellis task artifacts.
- Start the task before code edits.
- Read relevant Trellis specs and existing mutation script patterns.

## 2. Data Inspection

- Inspect prior mutation manifest/schema columns.
- Inspect representative 82-case artifact directories and summary JSON shapes.
- Confirm how source statements, ProblemSpecs, submissions, reports, and result
  signals are named.

## 3. Seed Inventory

- Implement `build_seed_inventory.py`.
- Generate `seed_inventory.{csv,json,md}`.
- Run `uv run python build_seed_inventory.py --check`.

## 4. Fault Applicability

- Implement `build_fault_family_applicability.py`.
- Generate `fault_family_applicability.{csv,json,md}`.
- Run `uv run python build_fault_family_applicability.py --check`.

## 5. Pilot Plan

- Implement `build_pilot_mutation_plan.py`.
- Generate `pilot_mutation_plan.{csv,json,md}`.
- Run `uv run python build_pilot_mutation_plan.py --check`.

## 6. Experiment-Pack Verification

- Run the research-experiment validator on the experiment pack.
- Record that missing future-stage execution/result files are expected if that
  remains the only validation failure.

## 7. Finish

- Review `git diff` in both OR-CI and OR-research repositories.
- Do not modify or revert unrelated `.mcp.json`.
- Commit the task artifacts and experiment scripts/outputs if validation passes.
