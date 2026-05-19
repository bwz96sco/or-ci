# OR-CI Gurobi ModelIR Extractor

## Goal

Implement ModelIR extraction for v1 linear Gurobi models so OR-CI can inspect what mathematical model a submission actually builds.

## Implementation Requirements

- Work in this standalone OR-CI repo.
- Support Gurobi linear objectives and linear constraints only.
- Call `model.update()` before reading variables, constraints, objective, and attributes.
- Use Gurobi APIs documented for v12:
  `model.getVars()`, `model.getConstrs()`, `model.getRow(constr)`, `model.getObjective()`, and `model.getAttr(...)`.

## ModelIR Contents

Record:

- variables: name, lower bound, upper bound, variable type
- objective: sense and linear coefficients by variable name
- constraints: name, sense, RHS, linear coefficients by variable name
- summary counts: variables, constraints, integer variables, binary variables

## Failure Handling

- If the model has unsupported objective/constraint features, return or raise an `UNSUPPORTED_MODEL_FEATURE` path that the verifier can classify.
- Do not optimize the model inside the extractor.

## Acceptance Criteria

- Tests prove extraction works for the handwritten BWOR fixture models.
- Constraint rows preserve coefficient signs and RHS values.
- Objective sense is reported as `min` or `max`.
- Extractor failures are classified without crashing the CLI.
