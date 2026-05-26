# Implement guarded mutation generator

## Goal

Implement the roadmap's guarded P0/P1 mutation generator path against the frozen mutation interface while preserving human seed-acceptance and equivalent-mutant gates.

## Confirmed Facts

- The notes experiment already has a mutation seed manifest, work queue,
  applicability matrix, operator backlog, plan preview, equivalent-mutant
  review template, and guarded runner preflight.
- Current mutation queue rows are all `run_eligible=false` because trusted seed
  models are still pending human source-fidelity acceptance.
- The roadmap requires P0/P1 real mutation-generator support, but actual
  mutation-study execution must remain blocked until seeds are human-accepted
  and equivalent mutants are reviewed.
- This task should edit research-note experiment scripts and generated
  experiment artifacts, not the OR-CI verifier package.

## Requirements

- Add a guarded generator stage for P0/P1 mutation plans under
  `experiments/or-ci-self-host-exploration-2026-05-25/`.
- Reuse the frozen queue, applicability, backlog, and plan-preview artifacts as
  inputs; do not duplicate their source-of-truth logic.
- Refuse to write a mutated artifact unless the queue row is
  `run_eligible=true`, the applicability row is `structurally_applicable`, the
  plan has an absolute JSON pointer and original/mutated values, and the output
  path stays under the planned mutation artifact directory.
- Preserve the current real-world gate: with today's queue, the generator must
  write zero mutated ProblemSpecs and produce only skip/preflight records.
- For future eligible rows, write a mutated ProblemSpec copy and a machine-readable
  mutation plan record without running OR-CI or setting any recall result.
- Record `equivalent_mutant_status=pending_review` for generated rows.
- Add a self-test or validation path that proves generation logic can mutate an
  eligible row in an isolated temporary directory without changing the real
  queue or producing paper-grade results.
- Update the roadmap/integration notes to show that the guarded generator stage
  is implemented but mutation execution remains blocked by human seed review.

## Out of Scope

- Human acceptance of seed models.
- Equivalent-mutant adjudication.
- OR-CI execution on generated mutants.
- Mutation recall estimates or paper-grade mutation results.
- Changes to the production `src/or_ci` verifier package.

## Acceptance Criteria

- [x] A generator script exists and can be run with `uv run python`.
- [x] Current generated records prove all 348 queued rows are skipped before
      artifact writing because no row is eligible yet.
- [x] Validation fails on stale/malformed generator outputs.
- [x] The isolated self-test demonstrates at least one eligible P0/P1 plan can
      produce a mutated ProblemSpec and plan JSON in a temporary directory.
- [x] Existing mutation scaffolds still pass their `--check` commands.
- [x] `uv run pytest` for OR-CI still passes or is reported if it cannot be run.
- [x] Roadmap task status is updated without claiming mutation-study completion.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
