# Guarded Mutation Generator Design

## Boundary

The generator belongs to the research notes experiment directory:

`/Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/or-ci-self-host-exploration-2026-05-25/`

It is not part of the OR-CI verifier package. It consumes already-frozen CSV/JSON
planning artifacts and writes research experiment artifacts only.

## Inputs

- `mutation-work-queue-2026-05-26.csv`
- `mutation-applicability-matrix-2026-05-26.csv`
- `mutation-operator-backlog-2026-05-26.csv`
- `mutation-plan-preview-2026-05-26.csv`

The plan preview remains the source of target JSON pointers and pre/post values
for P0/P1 rows. The generator does not discover new semantic targets.

## Generation Contract

For each row:

1. Join queue, applicability, backlog, and preview records by `mutation_id`.
2. Classify the row as skipped unless every gate passes:
   - `run_eligible=true`
   - `applicability_status=structurally_applicable`
   - priority is P0/P1
   - preview has an absolute JSON pointer
   - original value in the seed ProblemSpec matches the preview's recorded
     original value
   - output path resolves under the experiment's `mutations/` directory
3. For executable rows, deep-copy the seed ProblemSpec, apply the planned JSON
   pointer change, parse/serialize the mutated JSON, and write:
   - `mutations/<mutation_id>/problem.json`
   - `mutations/<mutation_id>/mutation-plan.json`
4. Record `equivalent_mutant_status=pending_review`.
5. Never run OR-CI and never write recall denominators or verifier outcomes.

## Current-State Behavior

Because the current queue has zero eligible rows, the generated record set must
contain only skip rows and no mutated ProblemSpecs. This is a positive guard
condition, not a failure.

## Validation

`--check` rebuilds expected records from the current source artifacts and
compares them to the committed generated outputs. It also runs an isolated
self-test using a temporary directory and a synthetic eligible copy of one
planned row, proving the write path works without modifying real experiment
state.

## Rollback

The generator is additive. Rollback is deleting the new generator script and its
generated `mutation-generation-records-*` artifacts, then reverting roadmap task
status text.
