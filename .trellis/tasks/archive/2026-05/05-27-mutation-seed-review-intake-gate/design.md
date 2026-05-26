# Build Mutation Seed Review Intake Gate Design

## Boundary

Implementation lives in the notes vault experiment directory:

`/Users/zhangbowen/Projects/OR/note/OR-research/experiments/or-ci-self-host-exploration-2026-05-25/`

No OR-CI verifier package code is changed.

## Data Flow

1. `mutation-seed-review-bundle-2026-05-27/` is distributed to a reviewer.
2. The reviewer returns a filled bundle-style `mutation-seed-review.csv`.
3. Operators place that CSV in a staging directory, not in the coordinator
   template path.
4. The intake script validates staged decisions by merging the staged review
   fields onto the canonical static seed rows and reusing the existing
   `build_mutation_seed_review.py` validation logic.
5. A row-scoped explicit promotion command copies only valid complete review
   fields into `mutation-seed-review-template-2026-05-27.csv`.
6. Existing seed review and mutation work-queue validators remain authoritative
   for whether seed acceptance can make mutation rows eligible.

## Contracts

Staged input is a CSV with the safe bundle shape:

- `seed_case_id`
- `packet_file`
- seed review fields from `build_mutation_seed_review.REVIEW_FIELDS`

Pending rows are allowed and stay non-promotable. Partial rows are validation
errors. Complete rows are validated against all existing seed-review rules.
`accept_seed` requires source fidelity accepted, final acceptance accepted,
materiality none, reviewer metadata/rationale, and no overlap with evaluation
sets.

## Safety

- Default and check modes never edit the coordinator review template.
- Promotion refuses missing staged rows, invalid rows, pending rows, partial
  rows, unknown seed IDs, and overwrite attempts.
- Promotion is seed-scoped so one valid returned decision can be advanced
  without accepting every staged row.
- No generated mutants or equivalent-mutant decisions are created.

## Integration

The human handoff and paper evidence-pack readiness should surface staged seed
review counts and continue to report mutation execution as blocked while
accepted seed count is zero.
