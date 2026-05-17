# OR-CI Integration Pilot Report

## Scope

- Producer: `or_llm_agent`
- Verifier: standalone OR-CI CLI through the editable `or-ci` dependency
- Model: `o3-mini`
- Problems: BWOR-001, BWOR-002, BWOR-010

## Summary

COMPLETED: at least one generated or reused submission reached OR-CI verification.

```json
{
  "total": 3,
  "classifications": {
    "SUCCESS": 3
  },
  "generation_statuses": {
    "generated": 3
  },
  "generation_modes": {
    "agent": 3
  }
}
```

## Matrix

| Problem | Mode | Generation | Agent RC | OR-CI Classification | Failure Check | Submission | Report |
|---|---|---|---:|---|---|---|---|
| BWOR-001 | `agent` | `generated` | `0` | `SUCCESS` | `-` | `submissions/BWOR-001.py` | `reports/BWOR-001.json` |
| BWOR-002 | `agent` | `generated` | `0` | `SUCCESS` | `-` | `submissions/BWOR-002.py` | `reports/BWOR-002.json` |
| BWOR-010 | `agent` | `generated` | `0` | `SUCCESS` | `-` | `submissions/BWOR-010.py` | `reports/BWOR-010.json` |

## Interpretation Notes

- `SUCCESS` means the generated submission passed the configured OR-CI invariants, not full model correctness.
- Semantic failures distinguish which verifier invariant failed first.
- Generation failures are reported separately from OR-CI classifications.
