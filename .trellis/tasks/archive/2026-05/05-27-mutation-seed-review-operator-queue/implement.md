# Mutation seed review operator queue Implementation Plan

## Checklist

1. Inspect existing seed manifest, bundle, intake, review readiness, work queue,
   handoff, paper-readiness, and roadmap artifacts.
2. Add `build_mutation_seed_review_operator_queue.py` in the self-host
   experiment directory.
3. Generate `mutation-seed-review-operator-queue-2026-05-27.{csv,json,md}`.
4. Wire the queue summary into `build_human_labeling_handoff.py` and
   `build_paper_evidence_pack_readiness.py`.
5. Update roadmap/reconciliation/sync notes to point mutation operators to the
   new queue.
6. Run validators:
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_mutation_seed_review.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_mutation_seed_review_intake.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_mutation_work_queue.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_mutation_seed_review_operator_queue.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_human_labeling_handoff.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python build_paper_evidence_pack_readiness.py --check`
   - notes and code `git diff --check`
7. Commit notes changes, run GitNexus change detection for the code repo, then
   archive and commit the Trellis task.

## Rollback Points

- Revert the new queue script and generated artifacts if source joins conflict
  with existing seed-review validators.
- Do not alter staged reviews, coordinator review template decisions, mutation
  work queue eligibility, generated mutants, or result templates in this task.

## Expected Current Outcome

The operator queue should report 29 pending human seed reviews, 0 staged
reviews, 0 accepted seeds, 0 run-eligible mutation rows, and no evidence claims.
