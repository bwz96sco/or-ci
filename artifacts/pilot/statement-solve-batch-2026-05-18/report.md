# Statement-Only Solve Batch Report

## Scope

- Producer: `or_llm_agent solve-batch --mode agent`
- Problems: BWOR-001, BWOR-002, BWOR-010
- Source: `--statements-dir` if supplied, otherwise `--dataset`

## Summary

```json
{
  "total": 3,
  "succeeded": 3,
  "failed": 0,
  "classifications": {
    "SUCCESS": 3
  },
  "spec_validation_statuses": {
    "passed": 3
  },
  "model_generation_statuses": {
    "generated": 3
  },
  "spec_fidelity_gate_statuses": {
    "manual_review_required": 3
  },
  "exit_codes": {
    "0": 3
  }
}
```

## Matrix

| Problem | Exit | Spec Validation | Attempts | Repair | Model Generation | Verification | Classification | Fidelity Gate | Artifact |
|---|---:|---|---:|---|---|---|---|---|---|
| BWOR-001 | `0` | `passed` | `1` | `not_needed` | `generated` | `PASS` | `SUCCESS` | `manual_review_required` | `BWOR-001` |
| BWOR-002 | `0` | `passed` | `1` | `not_needed` | `generated` | `PASS` | `SUCCESS` | `manual_review_required` | `BWOR-002` |
| BWOR-010 | `0` | `passed` | `1` | `not_needed` | `generated` | `PASS` | `SUCCESS` | `manual_review_required` | `BWOR-010` |

## Interpretation Notes

- `classification=SUCCESS` means the generated submission passed OR-CI checks against the generated spec.
- `spec_fidelity_gate_status=manual_review_required` means source-statement fidelity has not been certified.
- Inspect each case's `spec/fidelity-review.md` and `spec/fidelity-review.json` before treating generated specs as benchmark metadata.
