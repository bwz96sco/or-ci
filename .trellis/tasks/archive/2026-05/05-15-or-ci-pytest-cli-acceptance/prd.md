# OR-CI Pytest and CLI Acceptance

## Goal

Add the test suite and acceptance checks that prove the Phase 1 OR-CI micro-pilot works end to end.

## Implementation Requirements

- Work in this standalone OR-CI repo.
- Use pytest.
- Tests should run with:
  ```bash
  uv run pytest
  ```
- CLI acceptance should run with:
  ```bash
  uv run or-ci verify --problem <fixture_problem.json> --submission <fixture_model.py> --out <tmp_report.json>
  ```

## Required Test Coverage

- metadata loader rejects missing required fields
- verifier never passes `evaluation_only` into `build_model`
- ModelIR extraction returns expected variables, constraints, objective sense, and summary counts
- correct fixtures classify as `SUCCESS`
- syntax/runtime fixtures classify as `SYNTAX_OR_RUNTIME_ERROR`
- at least one wrong fixture classifies as `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL`
- CLI writes a valid report file

## Acceptance Criteria

- `uv run pytest` passes from this repo.
- Generated report JSON contains all required top-level fields.
- Tests avoid network calls and do not invoke LLM APIs.
- Tests are deterministic under the local Gurobi version pinned by the project.
