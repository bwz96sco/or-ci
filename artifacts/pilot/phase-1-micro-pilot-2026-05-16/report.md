# OR-CI Phase 1 Micro-Pilot Report

Date: 2026-05-16

## Decision

PASS: OR-CI Phase 1 micro-pilot is viable as a standalone verifier.

This pilot validates OR-CI alone, using handwritten BWOR metadata and handwritten correct/error/wrong submissions. It does not test `or_llm_agent` generation quality.

## Test Gate

- Command: `uv run pytest --junitxml artifacts/pilot/phase-1-micro-pilot-2026-05-16/pytest.xml`
- Result: 17 tests, 0 failures, 0 errors, 0 skipped
- Gurobi-backed tests ran successfully; no license skips occurred.

## Classification Matrix

| Problem | Submission | Expected | Observed | Match | JSON Report |
|---|---|---|---|---|---|
| BWOR-001 | `correct.py` | `SUCCESS` | `SUCCESS` | yes | `reports/BWOR-001-correct.json` |
| BWOR-001 | `runtime_error.py` | `SYNTAX_OR_RUNTIME_ERROR` | `SYNTAX_OR_RUNTIME_ERROR` | yes | `reports/BWOR-001-runtime_error.json` |
| BWOR-001 | `wrong.py` | `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` | `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` | yes | `reports/BWOR-001-wrong.json` |
| BWOR-002 | `correct.py` | `SUCCESS` | `SUCCESS` | yes | `reports/BWOR-002-correct.json` |
| BWOR-002 | `runtime_error.py` | `SYNTAX_OR_RUNTIME_ERROR` | `SYNTAX_OR_RUNTIME_ERROR` | yes | `reports/BWOR-002-runtime_error.json` |
| BWOR-002 | `wrong.py` | `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` | `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` | yes | `reports/BWOR-002-wrong.json` |
| BWOR-010 | `correct.py` | `SUCCESS` | `SUCCESS` | yes | `reports/BWOR-010-correct.json` |
| BWOR-010 | `runtime_error.py` | `SYNTAX_OR_RUNTIME_ERROR` | `SYNTAX_OR_RUNTIME_ERROR` | yes | `reports/BWOR-010-runtime_error.json` |
| BWOR-010 | `wrong.py` | `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` | `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` | yes | `reports/BWOR-010-wrong.json` |

## Observations

- Correct fixtures classified as `SUCCESS`: 3/3.
- Runtime-error fixtures classified as `SYNTAX_OR_RUNTIME_ERROR`: 3/3.
- Runnable-but-wrong fixtures classified as `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL`: 3/3.
- `SUCCESS` means no configured invariant failed; it is not a proof of full model correctness.
- The cost-scaling relation was strong enough to catch all current wrong fixtures because those fixtures hard-code unscaled objective coefficients.

## Objective Evidence

| Problem | Submission | Original Objective | Scaled Objective | Expected Scaled Objective |
|---|---|---:|---:|---:|
| BWOR-001 | `correct.py` | 5450 | 10900 | 10900 |
| BWOR-001 | `wrong.py` | 5450 | 5450 | 10900 |
| BWOR-002 | `correct.py` | 32.43589744 | 64.87179487 | 64.87179487 |
| BWOR-002 | `wrong.py` | 32.43589744 | 32.43589744 | 64.87179487 |
| BWOR-010 | `correct.py` | 425 | 850 | 850 |
| BWOR-010 | `wrong.py` | 425 | 425 | 850 |

## Next Decision

Proceed to the integration pilot with `or_llm_agent` as the producer and OR-CI as the verifier. Keep OR-CI standalone. The integration pilot should measure how generated submissions distribute across syntax/runtime errors, solver-status errors, runnable-but-wrong semantic failures, and successes.

Before scaling to 30-50 problems, add at least one additional semantic relation, such as constraint relaxation or symmetry permutation, because cost scaling only catches objective-coefficient-related wrongness.
