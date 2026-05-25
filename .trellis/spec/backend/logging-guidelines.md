# Logging Guidelines

> OR-CI is report-first: the JSON report is the primary operational output.

---

## Overview

OR-CI does not use an application logging framework in Phase 1. Verification
outcomes are structured data in the report written by
`uv run or-ci verify --problem <p.json> --submission <m.py> --out <r.json>`.
Console output is intentionally small and reserved for CLI validation messages.

The report schema is documented in `.trellis/spec/backend/data-contracts.md` and
implemented by `src/or_ci/report.py`.

---

## Output Channels

`--out <path.json>` is the canonical output for `or-ci verify`. It contains
`problem_id`, `submission`, `status`, `classification`, `solver_status`,
`model_ir_summary`, `checks`, `failures`, and `possible_causes`.

`stdout` is allowed for short success messages from non-report commands. The
implemented `validate-spec` command prints `valid problem metadata: <id>` when a
ProblemSpec is valid.

`stderr` is for CLI-level diagnostics such as invalid problem metadata in
`validate-spec` or missing CLI input files. Submission failures belong in the
JSON report, not stderr.

---

## Report-First Discipline

All submission outcomes must be represented in `VerificationReport`:

- syntax/import/build failures -> `SYNTAX_OR_RUNTIME_ERROR`
- non-optimal or mismatched required solver status -> `SOLVER_STATUS_ERROR`
- metamorphic, goal-programming, or scenario objective failures -> `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL`
- unsupported Gurobi features -> `UNSUPPORTED_MODEL_FEATURE`
- successful configured checks -> `SUCCESS`

Do not add a second log file beside the report. The report is the durable audit
artifact used by pilots and tests.

This discipline follows the archived report contract in
`.trellis/tasks/archive/2026-05/05-15-or-ci-data-contracts-cli-report/prd.md`.

---

## Information Leak Rules

OR-CI must not print or report evaluation labels as verifier evidence:

- Do not print `evaluation_only.answer`.
- Do not print `evaluation_only.label`.
- Do not pass `evaluation_only` into `build_model`.
- Do not dump full submitted source code on import or runtime failure.
- Do not make network calls, invoke LLM APIs, or expose provider errors.

The report intentionally has no field for `evaluation_only`. Failures should
describe verifier-observed behavior, such as solver status, objective values,
configured paths, and classification.

---

## Gurobi Output

Solver logs should be suppressed for deterministic CLI and test output. The
current verifier calls:

```python
set_param = getattr(model, "setParam", None)
if callable(set_param):
    set_param("OutputFlag", 0)
model.optimize()
```

Tests also configure the shared Gurobi environment with `OutputFlag = 0` in
`tests/conftest.py`.

Expose solver behavior through `solver_status`, `checks`, `failures`, and
`model_ir_summary`, not through raw Gurobi console output.

---

## Determinism

Reports should avoid wall-clock timestamps, random run IDs, machine-specific
temporary paths beyond the submitted path already recorded, or non-deterministic
ordering. `write_report` uses `json.dump(..., indent=2, sort_keys=True)` so
report keys are stable.

Tests must avoid network calls and LLM APIs, as required by
`.trellis/tasks/archive/2026-05/05-15-or-ci-pytest-cli-acceptance/prd.md`.

---

## What To Include In Reports

Include:

- classification and verification status
- original, scaled, relaxed, and scenario solver statuses
- objective values used by metamorphic, goal-programming, and scenario checks
- configured factors, paths, relations, goal weights, priorities, and tolerances
- ModelIR summary counts
- concise possible causes from `_possible_causes`

Keep `possible_causes` generic and actionable. Do not guess private modeler
intent beyond what checks observed.

---

## Anti-Patterns

- Do not use `print()` for submission failures; put them in `failures`.
- Do not leave Gurobi default verbose output enabled.
- Do not write separate `.log` files for a verification run.
- Do not log `evaluation_only` values anywhere.
- Do not paste submitted source code into stderr or reports.
- Do not add LLM/provider logs to OR-CI. Producer logs belong in
  `or_llm_agent`.
