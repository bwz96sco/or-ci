# Build mutation seed review intake gate

## Goal

Add a guarded staged intake gate for returned mutation seed-review decisions.
The gate must let reviewers return the safe bundle CSV without directly
editing the coordinator seed-review template, validate complete decisions
against the existing seed-review rules, and promote only valid complete rows
through an explicit command.

This advances the mutation-testing track without accepting seeds, generating
mutants, deciding equivalent mutants, running OR-CI, or estimating recall.

## Requirements

- Work in the notes vault under
  `experiments/packs/or-ci-self-host-exploration-2026-05-25/`.
- Reuse the existing seed candidate manifest, coordinator review template,
  seed-review readiness validator, seed-review bundle, and mutation work queue.
- Add a staging directory and readiness CSV/JSON/MD with one row per expected
  seed review.
- Default generation and `--check` must be read-only with respect to
  `mutation-seed-review-template-2026-05-27.csv`.
- Intake validation must reject unknown seed IDs, duplicate rows, stale or
  missing packet files, partial review decisions, invalid enum values,
  unsafe `accept_seed` combinations, and attempts to accept overlapping
  evaluation-set seeds.
- Promotion must require an explicit command and must refuse to overwrite
  existing coordinator decisions.
- Summaries must preserve non-claims: no seed is human accepted until promoted
  and existing mutation seed/work-queue validators pass; no mutation recall or
  equivalent-mutant evidence exists.
- Wire the new intake state into the human handoff, paper readiness, and
  roadmap/reconciliation notes.

## Acceptance Criteria

- [x] A new mutation seed review intake script exists in the experiment folder.
- [x] Running it without promotion writes deterministic readiness artifacts and
      does not edit the coordinator review template.
- [x] `--check` verifies readiness artifacts are current.
- [x] `--self-test` proves partial review and unsafe `accept_seed` rows are
      rejected.
- [x] An explicit promote command refuses the current pending state and leaves
      the coordinator template unchanged.
- [x] Existing mutation validators still pass:
      `build_mutation_seed_review.py --check`,
      `build_mutation_work_queue.py --check`, and
      `run_mutation_work_queue.py --check`.
- [x] Paper/handoff notes mention the staged seed-review intake gate while
      keeping mutation execution blocked.
- [x] No human labels, seed acceptances, generated mutants, equivalent-mutant
      decisions, OR-CI mutation results, or recall claims are fabricated.

## Notes

- This task only improves evidence intake safety for future human seed
  reviews. It does not complete the mutation blocker.
