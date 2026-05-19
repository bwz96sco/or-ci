# OR-CI Cost Scaling Verifier

## Goal

Implement the first metamorphic relation: scaling configured objective coefficient fields by a positive factor should preserve optimal status and scale the optimal objective value by that factor.

## Implementation Requirements

- Work in this standalone OR-CI repo.
- Deep-copy the metadata instance before applying transformations.
- Scale only numeric values under configured `coefficient_paths`.
- Rebuild the model by calling `build_model(scaled_instance)`.
- Optimize original and scaled models inside the verifier.

## Invariant

For positive factor `k`:

- original solver status must be optimal
- scaled solver status must be optimal
- `scaled_obj ≈ k * original_obj` using configured absolute/relative tolerance
- do not assert identical variable values

## Classification

- Syntax/import/build failures: `SYNTAX_OR_RUNTIME_ERROR`
- Non-optimal solver status where optimal is required: `SOLVER_STATUS_ERROR`
- Cost-scaling invariant failure: `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL`
- All checks passing: `SUCCESS`

## Acceptance Criteria

- Correct BWOR fixtures pass cost scaling.
- At least one wrong fixture fails cost scaling.
- Wrong fixtures that pass cost scaling are reported as coverage misses in tests, not treated as a framework bug.
- Report includes observed original/scaled objective values, factor, tolerance, expected relation, and likely causes.
