# Build baseline response intake gate Implementation Plan

## Checklist

1. Inspect existing baseline queue, response capture, results, manual bundle,
   and paper-readiness scripts.
2. Add `build_baseline_response_intake.py` in the notes experiment directory.
3. Generate staging directory/readiness artifacts without creating canonical
   responses.
4. Add self-tests for invalid JSON and model metadata mismatch.
5. Add explicit row-scoped promotion refusal/guard behavior and verify it
   leaves canonical artifacts unchanged when no valid staged response exists.
6. Wire the new intake state into roadmap/reconciliation/integration/report
   notes.
7. Run validators:
   - `uv run python build_baseline_response_intake.py --check`
   - `uv run python build_baseline_response_intake.py --self-test`
   - guarded promote refusal on a pending row
   - `uv run python build_baseline_response_capture.py --check`
   - `uv run python build_baseline_ablation_results.py --check`
   - paper evidence-pack readiness checks
   - `git diff --check`
8. Archive the Trellis task and commit notes plus Trellis bookkeeping
   separately if verification passes.

## Rollback Points

- Revert the new intake script and generated readiness artifacts if the intake
  contract conflicts with existing response capture.
- Do not alter canonical raw-response files or response template except through
  a successful explicit promotion path.

## Expected Current Outcome

Because no valid staged responses are expected yet, the initial readiness
status should remain pending/blocked for response evidence. This is correct:
the task adds safe intake machinery, not model evidence.
