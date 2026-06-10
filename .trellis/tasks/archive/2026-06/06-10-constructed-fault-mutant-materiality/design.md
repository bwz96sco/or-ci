# Design: Constructed Fault Mutants And Materiality

## Boundary

Implementation lives in the OR-research experiment pack:

`/Users/zhangbowen/Projects/OR/note/OR-research/experiments/constructed-source-fidelity-fault-benchmark-2026-06-10/`

OR-CI package code remains unchanged. The materiality runner invokes OR-CI via:

`uv run or-ci verify --problem <mutant-spec> --submission <original-submission> --out <report>`

## Data Flow

```text
pilot_mutation_plan.csv
  -> generate_pilot_mutants.py
  -> raw mutant artifact dirs + mutation_generation_ledger.*
  -> run_materiality_oracle.py
  -> OR-CI mutant reports + materiality_ledger.*
  -> execution_log.md + results_ledger.csv + claim_update.md
```

## Artifact Roots

Note-pack root:

`/Users/zhangbowen/Projects/OR/note/OR-research/experiments/constructed-source-fidelity-fault-benchmark-2026-06-10/`

Raw run-output root:

`/Users/zhangbowen/Projects/OR/code/or-ci/artifacts/experiments/constructed-source-fidelity-fault-benchmark-2026-06-10/`

Generated mutants use the directory declared by each planning row's
`planned_mutant_artifact_dir`.

## Mutant Generation Contract

Each generated artifact directory contains:

- `spec/problem.json`: evaluated mutant ProblemSpec;
- `spec/original_problem.json`: source ProblemSpec copy;
- `mutation_metadata.json`: mutation ID, fault family, target pointer,
  original value, mutated value, generation status, and source paths;
- `statement.txt`: copied source statement when available.

The evaluated `spec/problem.json` must not include `mutation_metadata` or
ground-truth labels.

## Operator Semantics

- `swap_or_perturb_objective_coefficient`: set the target value to the planned
  numeric replacement.
- `scale_unit_bearing_value_by_10x`: set the target value to the planned scaled
  replacement.
- `omit_one_action_index_or_year_signal`: replace the target list with the
  planned shortened list.
- `drop_one_period_or_scenario_signal`: replace the target list with the
  planned shortened list.
- `remove_or_disable_constraint_family_signal`: keep the JSON key and disable
  the constraint signal by recursively setting numeric values to `0` and
  booleans to `false`. This avoids conflating source-fidelity faults with
  missing-key runtime errors.

## Materiality Contract

For each generated mutant, parse the original OR-CI report and the mutant OR-CI
report. Classify:

- `material_valid`: original and mutant runs are valid and objective/status
  differs beyond tolerance;
- `silent_or_equivalent`: valid run but objective/status unchanged within
  tolerance;
- `solver_error_or_invalid_mutant`: metadata, runtime, unsupported feature, or
  solver status prevents materiality classification.

The primary pilot metric is `material_valid_mutant_count`.

## Research-Experiment Outputs

The runner writes:

- `execution_log.md`: exact commands, runner route, environment, status, paths;
- `results_ledger.csv`: required research-experiment columns for generation
  and materiality runs;
- `result_audit.md`: evidence integrity audit;
- `claim_ledger.csv`: claim-level traceability;
- `claim_update.md`: conservative route update.

## Tradeoffs

This implementation favors runnable mutants over pure deletion semantics for
dropped constraints. A true key deletion would measure parser robustness more
than source-fidelity detection. The metadata still records the intended fault
family and actual value transformation for later review.

## Rollback

All generated raw artifacts are confined to the constructed-fault raw output
root. To regenerate, rerun `generate_pilot_mutants.py` and
`run_materiality_oracle.py`. The scripts should rewrite only their own ledgers,
reports, and generated mutant directories.
