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
- `problem_type`: string, currently `LP` in fixtures.
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
linear structure.

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

The extractor uses Gurobi v12-style APIs: `model.getVars()`,
`model.getConstrs()`, `model.getRow(constr)`, `model.getObjective()`, and direct
or `getAttr` attribute reads. Unsupported features raise
`UnsupportedModelFeature` and map to `UNSUPPORTED_MODEL_FEATURE`.

Unsupported for the current verifier: SOS constraints, quadratic constraints,
general constraints, piecewise-linear objectives, quadratic objective terms, and
multiple objectives.

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

Current check names include `original_solver_status`, `cost_scaling`, and
`constraint_relaxation`.

`failures` contains structured dictionaries with at least a `check` and
`message` when a classification is not `SUCCESS`. `possible_causes` is generated
from `Classification` in `src/or_ci/verifier.py`.

---

## Metamorphic Checks Catalog

| Check | Metadata | Invariant | Failure Classification | Must Not Assert |
|---|---|---|---|---|
| `cost_scaling` | `metamorphic.cost_scaling` | Scaled model solves optimal and `scaled_obj ~= factor * original_obj`. | `SOLVER_STATUS_ERROR` for non-optimal scaled solve; `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` for objective mismatch. | Identical variable assignments. |
| `constraint_relaxation` | `metamorphic.constraint_relaxation` | Relaxed model solves optimal and objective satisfies configured `objective_relation`. | `SOLVER_STATUS_ERROR` for non-optimal relaxed solve; `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` for relation mismatch. | Full constraint equivalence or proof of complete correctness. |

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
| Objective sense | `min`, `max` |
| Check names | `original_solver_status`, `cost_scaling`, `constraint_relaxation` |
| Constraint-relaxation relations | `non_decrease`, `increase`, `non_increase`, `decrease` |
| Report output | JSON written by `or_ci.report.write_report` |
| Naming rule | BWOR only; never introduce NL4OR identifiers in OR-CI code, tests, fixtures, paths, or comments. |

Use these exact strings in ops specs, quality specs, tests, reports, and future
task PRDs.
