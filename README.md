# OR-CI

OR-CI stands for **Operations Research Continuous Integration**. It is a CI-style verification layer for operations-research model submissions.

It is not an OR solver or an LLM generation pipeline. It loads structured problem metadata, imports a submitted `build_model(data)` function, extracts a solver-backed model IR, runs semantic checks, classifies failures, and writes a report.

Phase 1 supports BWOR-style JSON metadata, Gurobi linear LP/MILP models, QP/MIQP quadratic objectives, ModelIR extraction, and deterministic verification checks. The first micro-pilot validates cost scaling; the continuation pilot adds constraint-relaxation checks for selected linear fixtures; the 2026-05-23 feature extension adds explicit goal-programming scalarization checks and multi-scenario status aggregation.

## Terminology

- **OR-CI**: Operations Research Continuous Integration. The package runs CI-style checks for submitted optimization model code.
- **ModelIR**: Optimization Model Intermediate Representation. It is the normalized representation OR-CI extracts from a solver model: variables, bounds, variable types, objective sense, linear and quadratic objective coefficients, constraints, senses, RHS values, and summary counts.
- **Submission**: A Python file exposing `build_model(data) -> gurobipy.Model`.
- **Metamorphic check**: A semantic test that transforms problem data in a controlled way and checks an expected relation, such as objective scaling under cost scaling or objective movement under constraint relaxation.

## CLI

```bash
uv run or-ci verify \
  --problem tests/fixtures/bwor/BWOR-002/problem.json \
  --submission tests/fixtures/bwor/BWOR-002/correct.py \
  --out report.json
```

## Tests

```bash
uv run pytest
```

## Pilot Artifacts

- First OR-CI-only micro-pilot: `artifacts/pilot/phase-1-micro-pilot-2026-05-16/`
- Constraint-relaxation continuation: `artifacts/pilot/phase-1-constraint-relaxation-2026-05-16/`
- Feature-family extension pilot: `artifacts/pilot/or-ci-feature-family-extensions-2026-05-23/`
