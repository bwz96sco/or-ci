# Source Fidelity Rubric Implementation Checklist

## Setup

- [x] Run Trellis before-dev guidance.
- [x] Run GitNexus impact analysis, or document that GitNexus CLI/MCP is unavailable and use local symbol/caller inspection.
- [x] Confirm `../or_llm_agent` worktree is clean before edits.

## Implementation

- [x] Add rubric constants and normalization helpers in `src/or_llm_agent/cli.py`.
- [x] Update fidelity agent prompt to require `source_fidelity_v1` dimensions.
- [x] Normalize review payloads into rubric-complete, legacy-flat, or rubric-incomplete outcomes.
- [x] Enforce hard-block dimension rejection and failed-verification guard.
- [x] Extend summary JSON fields for failed dimensions, warning/blocking counts, provisional flag, materiality, and rubric version.
- [x] Extend case fidelity markdown with a dimension table.
- [x] Add source-fidelity risk flags for known weak spots.
- [x] Add batch rubric aggregation helpers.
- [x] Write `fidelity-rubric-summary.json` and `fidelity-rubric-report.md` after batch review.
- [x] Link capstone artifacts from existing batch markdown when available.

## Tests

- [x] Update existing fidelity tests for rubric-complete agent payloads.
- [x] Add rubric-incomplete agent rejection coverage.
- [x] Add hard-block accepted-review coercion coverage.
- [x] Add legacy-flat manual compatibility coverage.
- [x] Add provisional clarification summary/report coverage.
- [x] Add risk-flag coverage for multi-scenario, routing/TSP, and unit-scaling weak spots where feasible with small fixtures.
- [x] Add batch capstone JSON/markdown coverage.

## Validation

Run from `../or_llm_agent`:

```bash
uv run pytest tests/test_problemspec_generation.py
uv run pytest tests
```

## Rollback Points

- Revert prompt and normalization helpers if agent review compatibility breaks.
- Revert capstone aggregation independently if per-case review behavior is correct but batch output fails.
