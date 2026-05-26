# Build Mutation Seed Review Intake Gate Implementation Plan

## Checklist

1. Inspect existing seed review, seed bundle, mutation work queue, and mutation
   run-record validators.
2. Add `build_mutation_seed_review_intake.py`.
3. Generate a staging directory with README and readiness CSV/JSON/MD.
4. Implement validation by translating bundle rows into coordinator rows and
   reusing existing seed-review validation.
5. Add self-tests for partial and unsafe acceptance rows.
6. Add explicit `--promote --seed-case-id <id>` and verify it refuses the
   current pending state without changing the coordinator template.
7. Wire intake status into human handoff and paper evidence-pack readiness;
   update roadmap/reconciliation notes.
8. Verify:
   - new intake generate/check/self-test;
   - promote refusal plus coordinator-template hash unchanged;
   - seed review/work queue/run preflight checks;
   - handoff and paper readiness checks;
   - `git diff --check`;
   - GitNexus detect changes before committing Trellis.
9. Commit notes, archive Trellis task, record session.

## Current Expected Outcome

The initial state should be pending: 29 expected seed rows, 0 staged complete
reviews, 0 promotable reviews, 0 accepted seeds, and mutation execution still
blocked.
