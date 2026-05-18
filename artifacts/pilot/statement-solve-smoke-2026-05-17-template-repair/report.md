# Metadata Template and Repair Smoke

## Scope

- Date: 2026-05-17
- Command: `or-llm-agent solve --mode agent`
- Input: `BWOR-010` natural-language statement
- Purpose: verify strict ProblemSpec template prompting and validation repair-loop plumbing.

## Result

| Problem | Spec Attempts | Spec Repair | Spec Validation | Model Generation | OR-CI Status | Classification |
|---|---:|---|---|---|---|---|
| `BWOR-010` | 1 | `not_needed` | `passed` | `generated` | `PASS` | `SUCCESS` |

## Fidelity Signal

The generated metadata preserved primitive objective components:

- `instance.unit_processing_profit`
- `instance.unit_transportation_cost`

The generated `cost_scaling.coefficient_paths` points to both primitive paths, rather than only to a precomputed net-benefit field. Constraint relaxation used valid OR-CI schema with `paths` and multiplicative `factor`.
