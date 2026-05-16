# OR-CI Phase 1 Constraint-Relaxation Continuation Report

Date: 2026-05-16

## Decision

PASS: OR-CI Phase 1 continuation is viable. The verifier now distinguishes objective-side wrong submissions from constraint-side wrong submissions on the handwritten BWOR pilot fixtures.

This continuation validates OR-CI alone. It does not test `or_llm_agent` generation quality.

## Test Gate

- Command: `uv run pytest --junitxml artifacts/pilot/phase-1-constraint-relaxation-2026-05-16/pytest.xml`
- Result: 21 tests, 0 failures, 0 errors, 0 skipped
- Gurobi-backed tests ran successfully; no license skips occurred.

## Classification Matrix

| Problem | Submission | Expected | Observed | Match | Failure Check | JSON Report |
|---|---|---|---|---|---|---|
| BWOR-001 | `correct.py` | `SUCCESS` | `SUCCESS` | yes | `-` | `reports/BWOR-001-correct.json` |
| BWOR-001 | `runtime_error.py` | `SYNTAX_OR_RUNTIME_ERROR` | `SYNTAX_OR_RUNTIME_ERROR` | yes | `submission` | `reports/BWOR-001-runtime_error.json` |
| BWOR-001 | `wrong.py` | `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` | `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` | yes | `cost_scaling` | `reports/BWOR-001-wrong.json` |
| BWOR-001 | `wrong_constraint.py` | `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` | `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` | yes | `constraint_relaxation` | `reports/BWOR-001-wrong_constraint.json` |
| BWOR-002 | `correct.py` | `SUCCESS` | `SUCCESS` | yes | `-` | `reports/BWOR-002-correct.json` |
| BWOR-002 | `runtime_error.py` | `SYNTAX_OR_RUNTIME_ERROR` | `SYNTAX_OR_RUNTIME_ERROR` | yes | `submission` | `reports/BWOR-002-runtime_error.json` |
| BWOR-002 | `wrong.py` | `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` | `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` | yes | `cost_scaling` | `reports/BWOR-002-wrong.json` |
| BWOR-002 | `wrong_constraint.py` | `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` | `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` | yes | `constraint_relaxation` | `reports/BWOR-002-wrong_constraint.json` |
| BWOR-010 | `correct.py` | `SUCCESS` | `SUCCESS` | yes | `-` | `reports/BWOR-010-correct.json` |
| BWOR-010 | `runtime_error.py` | `SYNTAX_OR_RUNTIME_ERROR` | `SYNTAX_OR_RUNTIME_ERROR` | yes | `submission` | `reports/BWOR-010-runtime_error.json` |
| BWOR-010 | `wrong.py` | `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` | `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` | yes | `cost_scaling` | `reports/BWOR-010-wrong.json` |
| BWOR-010 | `wrong_constraint.py` | `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` | `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` | yes | `constraint_relaxation` | `reports/BWOR-010-wrong_constraint.json` |

## Observations

- Expected classification matches: 12/12.
- Correct fixtures classified as `SUCCESS`: 3/3.
- Runtime-error fixtures classified as `SYNTAX_OR_RUNTIME_ERROR`: 3/3.
- Objective-wrong fixtures failed `cost_scaling`: 3/3.
- Constraint-wrong fixtures passed cost scaling and failed `constraint_relaxation`: 3/3.
- `SUCCESS` means no configured invariant failed; it is not a proof of full model correctness.

## Cost-Scaling Objective Evidence

| Problem | Submission | Check Status | Original Objective | Scaled Objective | Expected Scaled Objective |
|---|---|---|---:|---:|---:|
| BWOR-001 | `correct.py` | `PASS` | 5450 | 10900 | 10900 |
| BWOR-001 | `wrong.py` | `FAIL` | 5450 | 5450 | 10900 |
| BWOR-001 | `wrong_constraint.py` | `PASS` | 5450 | 10900 | 10900 |
| BWOR-002 | `correct.py` | `PASS` | 32.43589744 | 64.87179487 | 64.87179487 |
| BWOR-002 | `wrong.py` | `FAIL` | 32.43589744 | 32.43589744 | 64.87179487 |
| BWOR-002 | `wrong_constraint.py` | `PASS` | 32.43589744 | 64.87179487 | 64.87179487 |
| BWOR-010 | `correct.py` | `PASS` | 425 | 850 | 850 |
| BWOR-010 | `wrong.py` | `FAIL` | 425 | 425 | 850 |
| BWOR-010 | `wrong_constraint.py` | `PASS` | 425 | 850 | 850 |

## Constraint-Relaxation Objective Evidence

| Problem | Submission | Check Status | Relaxation | Original Objective | Relaxed Objective | Expected Relation |
|---|---|---|---|---:|---:|---|
| BWOR-001 | `correct.py` | `PASS` | `raw_limit_increase` | 5450 | 5995 | `increase` |
| BWOR-001 | `wrong_constraint.py` | `FAIL` | `raw_limit_increase` | 5450 | 5450 | `increase` |
| BWOR-002 | `correct.py` | `PASS` | `requirements_decrease` | 32.43589744 | 29.19230769 | `decrease` |
| BWOR-002 | `wrong_constraint.py` | `FAIL` | `requirements_decrease` | 32.43589744 | 32.43589744 | `decrease` |
| BWOR-010 | `correct.py` | `PASS` | `capacity_increase` | 425 | 492 | `increase` |
| BWOR-010 | `wrong_constraint.py` | `FAIL` | `capacity_increase` | 425 | 425 | `increase` |

## Next Decision

Proceed to an integration pilot with `or_llm_agent` as the producer and OR-CI as the verifier. Keep OR-CI standalone and measure generated submissions across syntax/runtime errors, solver-status errors, objective-side semantic failures, constraint-side semantic failures, and successes.
