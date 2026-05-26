# Baseline response operator queue Implementation Plan

## Checklist

1. Inspect existing manual submission, response intake, response capture,
   human handoff, paper-readiness, and roadmap artifacts.
2. Add `build_baseline_response_operator_queue.py` in the self-host experiment
   directory.
3. Generate `baseline-response-operator-queue-2026-05-27.{csv,json,md}`.
4. Wire the queue summary into `build_human_labeling_handoff.py` and
   `build_paper_evidence_pack_readiness.py`.
5. Update roadmap/reconciliation notes to point baseline operators to the new
   queue.
6. Run validators:
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_baseline_manual_submission_package.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_baseline_response_intake.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_baseline_response_capture.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_baseline_response_operator_queue.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_human_labeling_handoff.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_paper_evidence_pack_readiness.py --check`
   - notes and code `git diff --check`
7. Commit notes changes, run GitNexus change detection for the code repo, then
   archive and commit the Trellis task.

## Rollback Points

- Revert the new queue script and generated queue artifacts if the joined
  source contract conflicts with existing intake/capture validators.
- Do not alter staged responses, canonical raw responses, or the response
  template in this task.

## Expected Current Outcome

The operator queue should report 52 pending manual submissions, 0 staged
responses, 0 canonical responses, and no evidence claims.
