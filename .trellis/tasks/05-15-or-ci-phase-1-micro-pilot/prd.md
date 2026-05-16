# Implement OR-CI Phase 1 Micro-Pilot

## Goal

Implement the first OR-CI micro-pilot for BWOR: a standalone verifier that loads structured problem metadata, imports a handwritten Gurobi submission exposing `build_model(data) -> gurobipy.Model`, extracts a linear ModelIR, runs the cost-scaling metamorphic check, classifies failures, and writes a JSON report.

## Required Task Sequence

1. Complete `05-15-or-ci-data-contracts-cli-report`.
2. Complete `05-15-or-ci-gurobi-modelir-extractor`.
3. Complete `05-15-or-ci-cost-scaling-verifier`.
4. Complete `05-15-or-ci-bwor-micro-pilot-fixtures`.
5. Complete `05-15-or-ci-pytest-cli-acceptance`.

## Scope

- Work in this standalone OR-CI repo.
- `../or_llm_agent` may depend on OR-CI as an editable local package, but it must not own the OR-CI implementation.
- Use BWOR naming only; do not introduce NL4OR naming in new code, tests, or PRDs.
- Use JSON metadata, not YAML.
- Use handwritten fixtures for `BWOR-001`, `BWOR-002`, and `BWOR-010`.
- Keep v1 to Gurobi linear models.

## Acceptance Criteria

- `uv run or-ci verify --problem <problem.json> --submission <model.py> --out <report.json>` works from this repo.
- Correct fixtures return `SUCCESS`.
- Syntax/runtime fixtures return `SYNTAX_OR_RUNTIME_ERROR`.
- At least one wrong fixture returns `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL`.
- The verifier never passes `evaluation_only.answer` or labels into `build_model`.
- All Phase 1 tests pass with `uv run pytest`.

## Out of Scope

- LLM generation pipeline integration.
- Trellis check integration.
- Constraint relaxation, symmetry permutation, NLP, quadratic models, multi-objective models, and full 30-50 problem experiments.
