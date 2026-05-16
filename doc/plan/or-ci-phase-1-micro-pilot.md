# OR-CI Phase 1 Micro-Pilot Coding Plan

## Summary

Implement the first OR-CI micro-pilot for BWOR. The verifier should load structured problem metadata, import a handwritten Gurobi submission exposing `build_model(data) -> gurobipy.Model`, extract a linear ModelIR, run metamorphic verification, classify failures, and write a JSON report.

The initial Phase 1 pilot covers cost-scaling verification only. The continuation pilot adds constraint-relaxation verification for selected linear fixtures. This plan still does not include LLM generation, Trellis check integration, symmetry permutation, or the later 30-50 problem paper-scale experiment.

## Pilot Result and Continuation Scope

- The first OR-CI-only micro-pilot passed on 2026-05-16 with 17 pytest cases and 9 CLI report runs.
- The constraint-relaxation continuation passed on 2026-05-16 with 21 pytest cases and 12 CLI report runs.
- That pilot used handwritten BWOR metadata and handwritten submissions only. It did not test `or_llm_agent` generation quality.
- Cost scaling catches objective-coefficient mistakes, but it does not test whether constraints consume the intended instance fields.
- The continuation pilot adds a constraint-relaxation metamorphic check. It scales configured constraint-side numeric instance paths and checks a configured objective relation after rebuilding and optimizing the model.
- The integration pilot with `or_llm_agent` remains the next stage after the OR-CI-only verifier behavior is accepted.

## Terminology

- **OR-CI**: Operations Research Continuous Integration. OR-CI is a CI-style verification layer for optimization model submissions, not a solver or full modeling pipeline.
- **ModelIR**: Optimization Model Intermediate Representation. ModelIR is a normalized view of a submitted solver model, including variables, bounds, variable types, objective sense and coefficients, constraints, senses, RHS values, and summary counts.
- **Submission**: A Python file exposing `build_model(data) -> gurobipy.Model`.
- **Metamorphic check**: A semantic verification rule that transforms problem data and checks an expected relation in the optimized model outcome.

## Repository Layout

- Standalone implementation repo: `code/or-ci`
- Consumer / experiment repo: `code/or_llm_agent`
- Canonical dataset reference: `code/or_llm_agent/data/datasets/bwor.jsonl`
- Research notes:
  - `note/OR-research/ideas/or-ci-validation-plan.md`
  - `note/OR-research/ideas/or-ci-idea-refinement.md`

New OR-CI implementation work should happen in `code/or-ci`. The `code/or_llm_agent` repo should consume OR-CI as a package or CLI dependency when it needs to verify generated OR model submissions.

## Core Interfaces

### CLI

```bash
uv run or-ci verify \
  --problem path/to/problem.json \
  --submission path/to/model.py \
  --out path/to/report.json
```

### Submission Contract

```python
def build_model(data: dict) -> gurobipy.Model:
    ...
```

The submission returns an unoptimized Gurobi model. OR-CI is responsible for `model.update()`, ModelIR extraction, optimization, metamorphic checks, classification, and report writing.

### Metadata Format

Use JSON for Phase 1. Do not add YAML support yet.

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
    },
    "constraint_relaxation": {
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
  },
  "evaluation_only": {
    "answer": 32.43,
    "label": "correct"
  }
}
```

The verifier may read `evaluation_only` for report provenance, but must never pass it into `build_model`.

## Implementation Tasks

### 1. Data Contracts and CLI Report

- Add an `or_ci` package under `code/or-ci`.
- Add `[project.scripts]` entrypoint for `or-ci`.
- Implement JSON metadata loading, submission loading, classification enums, and report serialization.
- Report top-level fields:
  - `problem_id`
  - `submission`
  - `status`
  - `classification`
  - `solver_status`
  - `model_ir_summary`
  - `checks`
  - `failures`
  - `possible_causes`

### 2. Gurobi ModelIR Extractor

Support v1 linear Gurobi models only.

ModelIR should record:

- variables: name, lower bound, upper bound, variable type
- objective: sense and linear coefficients by variable name
- constraints: name, sense, RHS, linear coefficients by variable name
- summary counts: variables, constraints, integer variables, binary variables

Use Gurobi APIs:

- `model.update()`
- `model.getVars()`
- `model.getConstrs()`
- `model.getRow(constr)`
- `model.getObjective()`
- `model.getAttr(...)`

Do not optimize inside the extractor.

### 3. Cost-Scaling Verifier

For each configured positive factor `k`:

- Deep-copy `problem["instance"]`.
- Scale only numeric values under configured `coefficient_paths`.
- Rebuild the model with `build_model(scaled_instance)`.
- Optimize original and scaled models.
- Check:
  - original solver status is optimal
  - scaled solver status is optimal
  - `scaled_obj ~= k * original_obj` using configured tolerances

Do not require identical variable assignments.

### 3b. Constraint-Relaxation Verifier

For each configured relaxation:

- Deep-copy `problem["instance"]`.
- Scale only numeric values under configured constraint-side `paths`.
- Rebuild the model with `build_model(relaxed_instance)`.
- Optimize the relaxed model.
- Check:
  - relaxed solver status is optimal
  - relaxed objective satisfies the configured relation to the original objective

Supported objective relations:

- `increase`
- `non_decrease`
- `decrease`
- `non_increase`

This check is still metamorphic coverage, not full proof of model correctness. It is intended to catch submissions that hard-code capacities, requirements, limits, or similar constraint data.

### 4. BWOR Fixtures

Use handwritten fixtures for:

- `BWOR-001`: blending LP, maximization, candy factory
- `BWOR-002`: blending LP, minimization, feed mix
- `BWOR-010`: transportation/profit LP, maximization, flour allocation

For each problem, create:

- one `problem.json`
- one correct submission
- one syntax/runtime-error submission
- one runnable-but-wrong submission
- one runnable-but-wrong constraint submission for the continuation pilot

The `wrong.py` fixtures are expected to fail cost scaling. The `wrong_constraint.py` fixtures are expected to pass cost scaling but fail constraint relaxation.

### 5. Pytest and CLI Acceptance

Add pytest coverage for:

- metadata loader rejects missing required fields
- verifier passes only `instance` to `build_model`
- ModelIR extraction returns expected variables, constraints, objective sense, and summary counts
- correct fixtures classify as `SUCCESS`
- syntax/runtime fixtures classify as `SYNTAX_OR_RUNTIME_ERROR`
- at least one wrong fixture classifies as `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL`
- constraint-wrong fixtures pass cost scaling and fail `constraint_relaxation`
- CLI writes a valid report file

Run from `code/or-ci`:

```bash
uv run pytest
```

## Classifications

- `SUCCESS`
- `SYNTAX_OR_RUNTIME_ERROR`
- `SOLVER_STATUS_ERROR`
- `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL`
- `UNSUPPORTED_MODEL_FEATURE`

Passing means no tested invariant failed. It must not be reported as full model correctness.

## Assumptions

- Use BWOR naming only. Do not introduce new NL4OR identifiers.
- Phase 1 supports only Gurobi linear LP-style models.
- Ground-truth answers are allowed only in evaluation/test expectations, never in verifier inputs.
- Cost scaling catches only some wrong models. Constraint relaxation broadens coverage to selected constraint-side mistakes. Misses are coverage limits, not automatic failure of OR-CI.
- No network calls or LLM API calls are needed for Phase 1 tests.
