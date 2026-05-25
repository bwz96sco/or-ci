# Error Handling

> How OR-CI classifies broken submissions, solver failures, unsupported models,
> and semantic invariant failures.

---

## Overview

OR-CI treats every submitted Python file as untrusted input. The verifier should
return a classified `VerificationReport` for submission-level failures instead
of crashing the CLI. Fatal CLI argument problems and invalid problem metadata
are handled at the CLI boundary; model import/build/optimization/extraction
problems are captured in the report.

Canonical report fields and classification strings are defined in
`.trellis/spec/backend/data-contracts.md` and implemented in
`src/or_ci/contracts.py`.

---

## Failure Classification Taxonomy

| Classification | Emitted When | `failures` Content | Issue Type |
|---|---|---|---|
| `SUCCESS` | Original model, cost scaling, and optional constraint relaxation all pass. | Empty list. | No tested issue found. |
| `SYNTAX_OR_RUNTIME_ERROR` | Submission import fails, `build_model` is missing, `build_model` raises, configured scaling raises, or optimization raises before a solver status is available. | `{"check": "submission", "message": "...", "error_type": "..."}`. | Submission or problem/config issue. |
| `SOLVER_STATUS_ERROR` | Original, scaled, relaxed, or required scenario model reaches the wrong Gurobi status when a specific status is required. | `check`, `message`, transformed factor, relaxation name, scenario name, and observed solver status. | Submission/model issue or intentionally infeasible transformed instance. |
| `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` | Model runs, but a configured cost-scaling, constraint-relaxation, goal-programming, or scenario objective check fails. | `check`, `message`, observed objective values, configured tolerance, and transformation details. | Runnable semantic modeling issue. |
| `UNSUPPORTED_MODEL_FEATURE` | ModelIR extraction sees unsupported Gurobi features, such as quadratic constraints or multiple objectives, or sees quadratic objective terms without `problem_type` `QP`/`MIQP`. | `{"check": "model_ir", "message": "unsupported model features: ..."}`. | Out-of-scope model feature. |

The cost-scaling PRD names the core classifications in
`.trellis/tasks/archive/2026-05/05-15-or-ci-cost-scaling-verifier/prd.md`. The
ModelIR unsupported path is required by
`.trellis/tasks/archive/2026-05/05-15-or-ci-gurobi-modelir-extractor/prd.md`.

---

## Error Types

Use these exception classes at module boundaries:

- `MetadataError` in `src/or_ci/metadata.py`: invalid problem JSON shape.
- `SubmissionError` in `src/or_ci/submission.py`: missing file, failed import,
  or no callable `build_model(data)`.
- `ScalingError` in `src/or_ci/scaling.py`: configured path does not start with
  `instance` or scales no numeric values.
- `UnsupportedModelFeature` in `src/or_ci/model_ir.py`: Gurobi model uses a
  feature outside Phase 1 linear ModelIR support.

`MetadataError` is surfaced by `or-ci validate-spec` and by `or-ci verify` as a
CLI `SystemExit` before report writing, because invalid metadata means there is
no trustworthy problem contract. Submission and model errors are report-level
events.

---

## Isolation Rules

Submission import belongs in `src/or_ci/submission.py`:

```python
spec = importlib.util.spec_from_file_location(module_name, path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
build_model = getattr(module, "build_model", None)
```

Keep the generated module name unique by hashing the resolved file path, as the
current implementation does. This avoids accidental reuse when multiple
submissions share filenames.

Boundary handling:

- Import exceptions are wrapped as `SubmissionError` and later classified as
  `SYNTAX_OR_RUNTIME_ERROR`.
- Missing or non-callable `build_model` is `SubmissionError`.
- Exceptions from `build_model(...)`, `scale_numeric_paths(...)`, or
  `model.optimize()` before a solver status exists become
  `SYNTAX_OR_RUNTIME_ERROR`.
- Non-optimal Gurobi statuses after optimization become `SOLVER_STATUS_ERROR`,
  not runtime errors.
- `UnsupportedModelFeature` is caught separately before the broad submission
  exception handler and becomes `UNSUPPORTED_MODEL_FEATURE`.

---

## Deep-Copy Discipline

Never mutate shared problem metadata during verification. The verifier passes a
deep copy of `problem.instance` into the original model build:

```python
original_model = build_model(copy.deepcopy(problem.instance))
```

Metamorphic transformations also copy before editing. `scale_numeric_paths`
creates `scaled = copy.deepcopy(instance)` and then modifies only the copy.

This is required because OR-CI calls the same `build_model` function repeatedly
for original, scaled, and relaxed instances. In-place metadata mutation can leak
one transformation into the next check and produce false failures or false
passes.

---

## `evaluation_only` Discipline

`evaluation_only` may contain answer labels used by research evaluation, but it
must never reach the submitted model. The only data passed to submissions is the
`instance` subtree:

```python
build_model(copy.deepcopy(problem.instance))
```

Tests enforce this with sentinels in `tests/or_ci/test_verifier.py` and
`tests/or_ci/test_cli.py`; submissions raise if `evaluation_only`, `answer`, or
`label` appears in `data`.

The anti-leak rule is part of the archived Phase 1 PRD:
`.trellis/tasks/archive/2026-05/05-15-or-ci-phase-1-micro-pilot/prd.md`.

---

## Solver Status Handling

`_optimize` suppresses solver output, calls `model.optimize()`, reads
`model.Status`, and maps known Gurobi codes to names:

- `OPTIMAL` is the only passing solver status for original, scaled, and relaxed
  runs.
- `INFEASIBLE`, `INF_OR_UNBD`, `UNBOUNDED`, `TIME_LIMIT`, `NUMERIC`, and other
  non-optimal statuses become `SOLVER_STATUS_ERROR` when optimality is required.
- The original solve records `original_solver_status`.
- Cost-scaling transformed solves record keys like `scaled_2`.
- Constraint-relaxation transformed solves record keys like
  `relaxed_requirements_decrease`.

Only read objective values when `is_optimal` is true.

---

## Anti-Patterns

- Do not catch `Exception` and silently continue. Every caught submission
  failure must map to a `Classification` and report entry.
- Do not pass the full metadata dict to `build_model`; this leaks
  `evaluation_only`.
- Do not mutate `metadata["instance"]` or `problem.instance` in place during
  transformations.
- Do not call `model.optimize()` in `model_ir.py`; extraction must inspect
  structure only.
- Do not assert identical variable values between original and scaled runs; the
  cost-scaling invariant is objective-based.
- Do not classify unsupported quadratic constraints, general constraints, or
  multi-objective features as ordinary runtime errors. Use
  `UNSUPPORTED_MODEL_FEATURE`.
