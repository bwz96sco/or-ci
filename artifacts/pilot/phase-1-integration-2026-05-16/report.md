# OR-CI Integration Pilot Report

Date: 2026-05-16

## Scope

- Producer: `or_llm_agent`
- Verifier: standalone OR-CI CLI through the editable `or-ci` dependency
- Model: `o3-mini`
- Problems: BWOR-001, BWOR-002, BWOR-010

## Summary

BLOCKED: `or_llm_agent` reached the provider but no Python submissions were generated. See `summary.json` and `raw/*.txt` for sanitized provider errors.

```json
{
  "total": 3,
  "classifications": {
    "SYNTAX_OR_RUNTIME_ERROR": 3
  },
  "generation_statuses": {
    "failed": 3
  }
}
```

## Matrix

| Problem | Generation | OR-CI Classification | Failure Check | Submission | Report |
|---|---|---|---|---|---|
| BWOR-001 | `failed` | `SYNTAX_OR_RUNTIME_ERROR` | `submission` | `submissions/BWOR-001.py` | `reports/BWOR-001.json` |
| BWOR-002 | `failed` | `SYNTAX_OR_RUNTIME_ERROR` | `submission` | `submissions/BWOR-002.py` | `reports/BWOR-002.json` |
| BWOR-010 | `failed` | `SYNTAX_OR_RUNTIME_ERROR` | `submission` | `submissions/BWOR-010.py` | `reports/BWOR-010.json` |

## Interpretation Notes

- `SUCCESS` means the generated submission passed the configured OR-CI invariants, not full model correctness.
- Semantic failures distinguish which verifier invariant failed first.
- Generation failures are reported separately from OR-CI classifications.
