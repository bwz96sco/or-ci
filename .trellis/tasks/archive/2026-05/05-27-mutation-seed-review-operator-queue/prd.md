# Mutation seed review operator queue

## Goal

Add a row-level mutation seed-review operator queue in the notes vault. The
queue must join candidate seed rows, reviewer bundle packets, staged seed-review
intake state, coordinator seed-review state, and mutation work-queue eligibility
into one auditable action list.

This advances the mutation-testing track without accepting seeds, generating
mutants, deciding equivalent mutants, running OR-CI, or estimating mutation
recall.

## Requirements

- Work in the notes vault under
  `experiments/packs/or-ci-self-host-exploration-2026-05-25/`.
- Reuse the existing seed candidate manifest, seed-review bundle, staged
  seed-review intake readiness, coordinator seed-review readiness/template, and
  mutation work queue.
- Generate deterministic CSV, JSON, and Markdown artifacts that report one row
  per expected seed-review packet.
- Each row must include seed id, selection priority, overlap flags, packet
  file, staged review state, coordinator review state, current review decision,
  mutation work-queue eligibility preview, next operator action, blocker, and
  issue.
- The current no-review state must produce an explicit human-review action for
  all 29 rows, not an accepted-seed state.
- The queue must surface invalid or stale source states if bundle, intake,
  coordinator, or work-queue inputs disagree.
- Generated summaries must keep the current non-claims: no accepted seed,
  mutation generation, equivalent-mutant decision, OR-CI result, or recall
  estimate exists until human review and downstream validators pass.
- Wire the new queue into the human labeling handoff, paper evidence-pack
  readiness, roadmap, and reconciliation notes.

## Acceptance Criteria

- [x] `build_mutation_seed_review_operator_queue.py` exists in the self-host
      experiment directory and supports generation plus `--check`.
- [x] The generated CSV/JSON/MD queue reports 29 rows and status
      `pending_human_seed_reviews` in the current state.
- [x] All 29 current rows have next action
      `review_seed_packet_and_stage_returned_csv`.
- [x] `--check` fails on stale generated artifacts and passes after
      regeneration.
- [x] Existing seed review, seed-review intake, mutation work queue, human
      handoff, and paper evidence-pack readiness checks still pass.
- [x] Roadmap/reconciliation/readiness notes reference the operator queue while
      keeping mutation execution and recall evidence blocked.
- [x] No human seed acceptance, mutant generation, equivalent-mutant decision,
      OR-CI result, or mutation-recall claim is fabricated.

## Notes

- This is support automation for the mutation seed-review gate. It does not
  resolve the human-review dependency.
