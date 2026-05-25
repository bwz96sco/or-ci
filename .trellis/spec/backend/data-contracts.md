# Data Contracts

> Public data contracts that flow across OR-CI module boundaries: problem
> metadata, submission interface, ModelIR, and verification report.

---

## Overview

OR-CI boundary data is intentionally small and explicit:

- Input problem metadata is JSON loaded by `src/or_ci/metadata.py` into
  `ProblemMetadata`.
- A submitted Python file exposes `def build_model(data: dict) -> gurobipy.Model`.
- `src/or_ci/model_ir.py` extracts a linear `ModelIR` from the built Gurobi model.
- `src/or_ci/verifier.py` returns `VerificationReport`, and `src/or_ci/report.py`
  serializes it as JSON.

The original public contract was defined by
`.trellis/tasks/archive/2026-05/05-15-or-ci-data-contracts-cli-report/prd.md`.
The implemented dataclasses and Enums now live in `src/or_ci/contracts.py`.

---

## Problem Metadata Schema

Problem metadata is a JSON object with these top-level fields:

```json
{
  "id": "BWOR-002",
  "problem_type": "LP",
  "instance": {},
  "metamorphic": {
    "cost_scaling": {
      "coefficient_paths": ["instance.price"],
      "factors": [2.0],
      "tolerance_abs": 1e-6,
      "tolerance_rel": 1e-6
    }
  },
  "evaluation_only": {
    "answer": 32.43,
    "label": "correct"
  }
}
```

Required top-level fields:

- `id`: string problem ID, currently `BWOR-NNN`.
- `problem_type`: one of `LP`, `MILP`, `QP`, `MIQP`, or `MULTI_SCENARIO`.
- `instance`: object passed to `build_model`.
- `metamorphic`: object containing verifier check configuration.

Optional top-level field:

- `evaluation_only`: object retained by the metadata loader but never passed to
  `build_model`.

### `metamorphic.cost_scaling`

`cost_scaling` is required. It contains:

- `coefficient_paths`: non-empty list of string paths beginning with `instance`.
- `factors`: non-empty list of positive numbers.
- `tolerance_abs`: non-negative number, default `1e-6`.
- `tolerance_rel`: non-negative number, default `1e-6`.

The verifier deep-copies `instance`, scales every configured numeric value by
each factor, rebuilds the model, and checks
`scaled_obj ~= factor * original_obj`. Do not assert identical variable values;
the cost-scaling PRD explicitly scoped the invariant to objective values.

### `metamorphic.constraint_relaxation`

`constraint_relaxation` is optional but implemented. It contains:

```json
{
  "relaxations": [
    {
      "name": "requirements_decrease",
      "paths": ["instance.requirements"],
      "factor": 0.9,
      "objective_relation": "decrease"
    }
  ],
  "tolerance_abs": 1e-6,
  "tolerance_rel": 1e-6
}
```

Fields:

- `relaxations`: non-empty list of relaxation specs.
- `name`: non-empty string. It is used in `solver_status` keys such as
  `relaxed_requirements_decrease`.
- `paths`: non-empty list of string paths beginning with `instance`.
- `factor`: positive number applied to every numeric value under each path.
- `objective_relation`: one of `non_decrease`, `increase`, `non_increase`, or
  `decrease`.
- `tolerance_abs`: non-negative number, default `1e-6`.
- `tolerance_rel`: non-negative number, default `1e-6`.

Older 2026-05-16 spec PRDs describe this as "emerging"; the current
implementation and fixtures now make the schema concrete in
`src/or_ci/metadata.py`, `src/or_ci/verifier.py`, and
`tests/fixtures/bwor/*/problem.json`.

### `metamorphic.goal_programming`

`goal_programming` is optional. It records an explicit scalarization contract for
generated goal-programming models. OR-CI supports only submitted single-objective
Gurobi models; native Gurobi multi-objective models are still unsupported.

Weighted mode:

```json
{
  "mode": "weighted",
  "objective_sense": "min",
  "goals": [
    {
      "name": "profit_deviation",
      "expression": {"variables": {"d_profit": 1.0}, "constant": 0.0},
      "weight": 3.0
    }
  ],
  "tolerance_abs": 1e-6,
  "tolerance_rel": 1e-6
}
```

Lexicographic mode:

```json
{
  "mode": "lexicographic",
  "objective_sense": "min",
  "goals": [
    {
      "name": "priority_1",
      "expression": {"variables": {"d1": 1.0}},
      "priority": 1,
      "priority_weight": 100.0
    },
    {
      "name": "priority_2",
      "expression": {"variables": {"d2": 1.0}},
      "priority": 2,
      "priority_weight": 1.0
    }
  ]
}
```

Validation rules:

- `mode` is `weighted` or `lexicographic`.
- `objective_sense` is `min` or `max`.
- weighted goals require positive `weight`.
- lexicographic goals require unique positive integer `priority` and positive
  `priority_weight`.
- lexicographic `priority_weight` values must strictly decrease as priority
  numbers increase.
- goal expressions are linear over submitted model variable names.

The verifier checks that the submitted model objective sense, linear objective
coefficients, objective constant, and optimized objective value match the
configured scalarization. It reports per-goal achieved values in the
`goal_programming` check details.

### Multi-Scenario Problems

`problem_type = MULTI_SCENARIO` uses a top-level `scenarios` array instead of a
single required top-level `instance`/`metamorphic` pair:

```json
{
  "id": "BWOR-032",
  "problem_type": "MULTI_SCENARIO",
  "scenarios": [
    {
      "name": "base_infeasible",
      "instance": {},
      "expected_solver_status": "INFEASIBLE"
    },
    {
      "name": "rental_feasible",
      "instance": {},
      "expected_solver_status": "OPTIMAL",
      "objective": {"value": 10.0, "relation": "equal"},
      "metamorphic": {
        "cost_scaling": {
          "coefficient_paths": ["instance.objective"],
          "factors": [2.0]
        }
      }
    }
  ]
}
```

Each scenario may include:

- `problem_type`: `LP`, `MILP`, `QP`, or `MIQP`; defaults to `LP`.
- `expected_solver_status`: one of the supported Gurobi status names.
- `objective`: optional objective check with relation `equal`, `non_decrease`,
  `increase`, `non_increase`, or `decrease`.
- `metamorphic`: optional scenario-level `cost_scaling`,
  `constraint_relaxation`, and `goal_programming` checks.
- `required`: boolean, default `true`.

The aggregate report passes only when all required scenarios satisfy their
expected solver status and configured scenario-level checks.

---

## Submission Contract

A submission is a Python file that exposes:

```python
def build_model(data: dict) -> gurobipy.Model:
    ...
```

`data` is a deep copy of the metadata `instance` subtree, not the whole metadata
object. It must not contain `evaluation_only`, `answer`, or `label`.

`build_model` should construct and return an unoptimized `gurobipy.Model`. It may
read only the supplied instance values. OR-CI calls `build_model` repeatedly for
the original instance and transformed instances, so submissions must not rely on
global mutable state that changes model semantics across calls.

The import boundary is `src/or_ci/submission.py`: `load_build_model` imports the
file with `importlib.util.spec_from_file_location`, checks that `build_model` is
callable, and returns it.

---

## ModelIR

`ModelIR` is the normalized Optimization Model Intermediate Representation
extracted from a Gurobi model before semantic checks continue. The extractor
calls `model.update()` and rejects unsupported model features before reading
supported structure.

Shape:

- `variables`: list of `VariableIR`
  - `name`
  - `lower_bound`
  - `upper_bound`
  - `variable_type`
- `objective`: `ObjectiveIR`
  - `sense`: `min` or `max`
  - `coefficients`: variable-name to coefficient mapping
  - `constant`
  - `quadratic_terms`: list of `{var1, var2, coefficient}` terms for QP/MIQP
    quadratic objectives
- `constraints`: list of `ConstraintIR`
  - `name`
  - `sense`
  - `rhs`
  - `coefficients`: variable-name to coefficient mapping
- `summary`: object with integer counts:
  - `variables`
  - `constraints`
  - `integer_variables`
  - `binary_variables`
  - `quadratic_objective_terms`

The extractor uses Gurobi v12-style APIs: `model.getVars()`,
`model.getConstrs()`, `model.getRow(constr)`, `model.getObjective()`, and direct
or `getAttr` attribute reads. Unsupported features raise
`UnsupportedModelFeature` and map to `UNSUPPORTED_MODEL_FEATURE`.

Unsupported for the current verifier: SOS constraints, quadratic constraints,
general constraints, piecewise-linear objectives, and multiple objectives.
Quadratic objective terms are supported only when `problem_type` is `QP` or
`MIQP`.

---

## Report JSON

`VerificationReport.to_dict()` serializes to JSON with exactly these top-level
fields:

- `problem_id`
- `submission`
- `status`
- `classification`
- `solver_status`
- `model_ir_summary`
- `checks`
- `failures`
- `possible_causes`

`status` is `PASS` only when `classification` is `SUCCESS`; otherwise it is
`FAIL`. Passing means no configured invariant failed. It does not mean the model
is fully mathematically correct.

`checks` is a list of `CheckResult` objects:

- `name`
- `status`
- `details`

Current check names include `original_solver_status`, `cost_scaling`,
`constraint_relaxation`, `goal_programming`, `scenario_solver_status`,
`scenario_objective`, `scenario_goal_programming`, `scenario_cost_scaling`, and
`scenario_constraint_relaxation`.

`failures` contains structured dictionaries with at least a `check` and
`message` when a classification is not `SUCCESS`. `possible_causes` is generated
from `Classification` in `src/or_ci/verifier.py`.

---

## Metamorphic Checks Catalog

| Check | Metadata | Invariant | Failure Classification | Must Not Assert |
|---|---|---|---|---|
| `cost_scaling` | `metamorphic.cost_scaling` | Scaled model solves optimal and `scaled_obj ~= factor * original_obj`. | `SOLVER_STATUS_ERROR` for non-optimal scaled solve; `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` for objective mismatch. | Identical variable assignments. |
| `constraint_relaxation` | `metamorphic.constraint_relaxation` | Relaxed model solves optimal and objective satisfies configured `objective_relation`. | `SOLVER_STATUS_ERROR` for non-optimal relaxed solve; `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` for relation mismatch. | Full constraint equivalence or proof of complete correctness. |
| `goal_programming` | `metamorphic.goal_programming` | Submitted objective sense, coefficients, constant, and optimized objective match the configured scalarization. | `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` for mismatch. | Native multi-objective proof or hidden goal semantics. |
| `scenario_solver_status` | top-level `scenarios` | Each required scenario reaches its configured solver status. | `SOLVER_STATUS_ERROR` for status mismatch. | Equivalence between scenarios beyond configured checks. |

The cost-scaling behavior follows
`.trellis/tasks/archive/2026-05/05-15-or-ci-cost-scaling-verifier/prd.md`. The
constraint-relaxation behavior is implemented in the current code and exercised
by `wrong_constraint.py` fixtures.

---

## Canonical Vocabulary

| Concept | Canonical Values |
|---|---|
| Problem ID format | `BWOR-NNN` |
| Submission function | `build_model(data: dict) -> gurobipy.Model` |
| Verification status | `PASS`, `FAIL` |
| Classification | `SUCCESS`, `SYNTAX_OR_RUNTIME_ERROR`, `SOLVER_STATUS_ERROR`, `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL`, `UNSUPPORTED_MODEL_FEATURE` |
| Problem type | `LP`, `MILP`, `QP`, `MIQP`, `MULTI_SCENARIO` |
| Objective sense | `min`, `max` |
| Check names | `original_solver_status`, `cost_scaling`, `constraint_relaxation`, `goal_programming`, `scenario_solver_status`, `scenario_objective`, `scenario_goal_programming`, `scenario_cost_scaling`, `scenario_constraint_relaxation` |
| Constraint-relaxation relations | `non_decrease`, `increase`, `non_increase`, `decrease` |
| Goal-programming modes | `weighted`, `lexicographic` |
| Report output | JSON written by `or_ci.report.write_report` |
| Naming rule | BWOR only; never introduce NL4OR identifiers in OR-CI code, tests, fixtures, paths, or comments. |

Use these exact strings in ops specs, quality specs, tests, reports, and future
task PRDs.
