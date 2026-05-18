# Statement-Only Agent-Mode Smoke Pilot

## Scope

- Date: 2026-05-17
- Producer: `or_llm_agent solve --mode agent`
- Verifier: standalone OR-CI CLI through the editable `or-ci` dependency
- Inputs: natural-language BWOR statements only
- Problems: `BWOR-001`, `BWOR-002`, `BWOR-010`

## Result Matrix

| Problem | Spec Validation | Model Generation | OR-CI Status | Classification | Fidelity Review |
|---|---|---|---|---|---|
| `BWOR-001` | `passed` | `generated` | `PASS` | `SUCCESS` | `spec/fidelity-review.md` |
| `BWOR-002` | `passed` | `generated` | `PASS` | `SUCCESS` | `spec/fidelity-review.md` |
| `BWOR-010` | `passed` | `generated` | `PASS` | `SUCCESS` | `spec/fidelity-review.md` |

## Manual Fidelity Notes

- `BWOR-001`: generated `instance` and metamorphic checks match the trusted fixture structure and values. Constraint relaxation covers `instance.raw_limit`.
- `BWOR-002`: generated `instance` and metamorphic checks match the trusted fixture structure and values. Constraint relaxation covers `instance.requirements`.
- `BWOR-010`: generated data are semantically faithful to the statement and solve correctly, but the generated spec uses `unit_net_benefit = processing profit - transport cost` instead of preserving separate `profit` and `transport_cost` primitive fields as in the trusted fixture. This is acceptable for this smoke, but it weakens separate objective-component traceability.

## Prompt Repair During Pilot

The first `BWOR-010` attempt failed schema validation before model generation:

```text
invalid problem metadata: constraint_relaxation.relaxation_0.paths must be a non-empty list
```

The generated spec used `path`/`direction`/`amount`; OR-CI requires `paths` plus multiplicative `factor`. The prompt was tightened with the exact `constraint_relaxation.relaxations[]` schema, and the rerun passed end to end. The failing run is preserved in `BWOR-010-before-prompt-fix/`.

## Interpretation

This pilot verifies that the current statement-only flow can run:

1. natural-language statement to OR-CI ProblemSpec,
2. OR-CI metadata validation,
3. ProblemSpec to Gurobi `build_model`,
4. OR-CI metamorphic verification.

OR-CI PASS means the generated model satisfies invariants against the generated spec. It is not, by itself, proof that the generated spec fully preserves the original statement. Manual or automated spec-fidelity review remains a required decision gate.

## Recommended Next Change

Tighten ProblemSpec generation so objective inputs preserve primitive statement quantities where practical, for example separate `profit` and `transport_cost` instead of only precomputed `net_benefit`. This would make OR-CI metamorphic checks better aligned with statement-level semantics and easier to audit.
