# Mutation seed review operator queue Design

## Boundaries

Implementation lives in the OR research notes vault:

`/Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/or-ci-self-host-exploration-2026-05-25/`

The OR-CI verifier package is not modified. The code repo receives only
Trellis task lifecycle artifacts.

## Data Flow

1. `mutation-seed-candidate-manifest-2026-05-26.csv` defines the 29 candidate
   seeds and their overlap/feature metadata.
2. `mutation-seed-review-bundle-2026-05-27/` contains one human-facing packet
   per seed plus the blank returned-review CSV.
3. `mutation-seed-review-intake-readiness-2026-05-27.csv` reports staged
   returned-review state before promotion.
4. `mutation-seed-review-template-2026-05-27.csv` and
   `mutation-seed-review-readiness-2026-05-27.json` report coordinator review
   state after explicit promotion.
5. `mutation-work-queue-2026-05-26.csv/json` reports whether any mutation rows
   are run-eligible after seed review.
6. The new operator queue joins those sources by `seed_case_id`.

## Current-State Contract

There are currently no staged reviews, no promoted reviews, and no accepted
seeds. Therefore every seed row should direct the operator to review the seed
packet and stage the returned CSV through the intake gate.

If a future row has a complete valid staged review, the next action becomes
explicit promotion. If a future row is accepted and mutation rows become
run-eligible, the next action becomes mutation queue validation. Invalid
staged/coordinator/source states take precedence.

## Safety Properties

- The queue is coordination-only and never writes seed-review decisions.
- The queue does not promote staged reviews.
- The queue does not mark seeds accepted, generate mutants, classify equivalent
  mutants, run OR-CI, or compute recall.
- Overlap and invalid accepted-seed states remain blockers surfaced from the
  existing validators.

## Reporting Integration

The human handoff and paper-readiness outputs should surface the operator queue
as the mutation seed-review execution map. Roadmap and reconciliation notes
should continue to state that mutation execution is blocked until human-accepted
trusted seeds and equivalent-mutant decisions exist.
