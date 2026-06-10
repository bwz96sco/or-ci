# Implementation Plan

## 1. Planning Gate

- Validate `prd.md`, `design.md`, `implement.md`, `implement.jsonl`, and
  `check.jsonl`.
- Start the Trellis task before code edits.

## 2. Pre-Development Context

- Load Trellis package/spec guidance.
- Inspect existing constructed-fault scripts and OR-CI CLI contracts.
- Confirm no OR-CI package symbol edit is needed.

## 3. Mutant Generator

- Add `generate_pilot_mutants.py`.
- Reuse helpers from `constructed_fault_common.py` when possible.
- Generate raw mutant artifact directories from `pilot_mutation_plan.csv`.
- Write `mutation_generation_ledger.{csv,json,md}`.
- Run:
  `PYTHONDONTWRITEBYTECODE=1 uv run python generate_pilot_mutants.py --check`

## 4. Materiality Oracle

- Add `run_materiality_oracle.py`.
- Invoke `uv run or-ci verify` for each generated mutant.
- Parse original and mutant reports.
- Write `materiality_ledger.{csv,json,md}`.
- Write `execution_log.md`, `results_ledger.csv`, `result_audit.md`,
  `claim_ledger.csv`, and `claim_update.md`.
- Run:
  `PYTHONDONTWRITEBYTECODE=1 uv run python run_materiality_oracle.py --check`

## 5. Validation

- Run both scripts in generate mode and check mode.
- Run:
  `PYTHONDONTWRITEBYTECODE=1 uv run python -m py_compile ...`
- Run:
  `uv run pytest`
- Run:
  `uv run python <research-experiment>/scripts/validate_experiment_pack.py <pack-root>`
- Run GitNexus change detection before OR-CI Trellis commits.

## 6. Finish

- Review diffs in OR-research and OR-CI.
- Leave unrelated `.mcp.json` untouched.
- Commit OR-research artifacts.
- Commit/archive/journal Trellis task in OR-CI.
