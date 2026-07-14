# Build constructed fault mutant generator and materiality oracle

## Goal

Turn the existing side-effect-free pilot plan into executable evidence:

1. generate concrete mutant ProblemSpec artifacts from
   `pilot_mutation_plan.csv`;
2. run the original submission against each mutant spec through OR-CI;
3. classify materiality by comparing original and mutant solver status/objective;
4. write research-experiment execution/result artifacts that downstream
   acceptance-layer work can consume.

This task implements the run-matrix rows `pilot_mutant_generation_3x5` and
`pilot_materiality_oracle`. It does not evaluate LLM judges or the full layered
workflow.

## Requirements

- Add deterministic Python scripts under:
  `/Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10/`.
- Read the existing planning outputs:
  - `seed_inventory.csv`;
  - `pilot_mutation_plan.csv`;
  - original ProblemSpec and submission paths referenced by those files.
- Generate one mutant artifact directory per row in `pilot_mutation_plan.csv`.
- Generated mutant artifacts must include:
  - mutated `spec/problem.json`;
  - original `spec/original_problem.json`;
  - `mutation_metadata.json`;
  - copied source statement or a path reference to it;
  - no mutation metadata inside the evaluated ProblemSpec itself.
- Mutation operators must preserve schema validity where possible:
  - objective and unit-scaling rows replace the planned target value;
  - action/period omission rows replace the planned dimension list;
  - dropped-constraint rows disable numeric demand/requirement signals while
    retaining the JSON key, to avoid turning every drop into a KeyError.
- Write generated mutation ledgers:
  - `mutation_generation_ledger.csv`;
  - `mutation_generation_ledger.json`;
  - `mutation_generation_ledger.md`.
- Add a materiality runner that invokes OR-CI with `uv run or-ci verify` for
  each generated mutant and writes per-mutant reports under the raw experiment
  artifact root.
- Write materiality outputs:
  - `materiality_ledger.csv`;
  - `materiality_ledger.json`;
  - `materiality_ledger.md`.
- Write research-experiment Stage 05/06 outputs:
  - `execution_log.md`;
  - `results_ledger.csv`;
  - `result_audit.md`;
  - `claim_ledger.csv`;
  - `claim_update.md`.
- Every new script must support `--check`.
- Preserve caveats:
  - generated mutants are constructed evidence, not natural-distribution
    samples;
  - materiality is solve-comparison evidence, not human source-fidelity labels;
  - invalid and silent/equivalent mutants must not enter material denominators.
- Do not modify OR-CI verifier/package internals for this task.

## Acceptance Criteria

- [ ] Trellis planning artifacts describe scope, data contracts, non-goals, and
      validation.
- [ ] `generate_pilot_mutants.py` writes and checks concrete mutant artifacts
      plus `mutation_generation_ledger.{csv,json,md}`.
- [ ] `run_materiality_oracle.py` writes and checks
      `materiality_ledger.{csv,json,md}` and OR-CI mutant reports.
- [ ] `execution_log.md`, `results_ledger.csv`, `result_audit.md`,
      `claim_ledger.csv`, and `claim_update.md` are created with traceable
      evidence paths.
- [ ] At least 10 generated mutant artifacts exist if the 15-row pilot remains
      runnable.
- [ ] Materiality ledger separates `material_valid`, `silent_or_equivalent`,
      and `solver_error_or_invalid_mutant` denominator buckets.
- [ ] `PYTHONDONTWRITEBYTECODE=1 uv run python <script> --check` passes for
      the new scripts.
- [ ] `uv run pytest` passes in OR-CI.
- [ ] `validate_experiment_pack.py` passes for the experiment pack.
- [ ] GitNexus change detection is run before committing OR-CI Trellis changes.

## Notes

- This task intentionally uses OR-CI as a black-box verifier through its CLI.
- If a mutant fails because the original submission cannot run against the
  mutated instance, record it as invalid rather than hiding it.
