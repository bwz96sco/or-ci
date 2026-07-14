# NL4OPT external label agreement analyzer

## Goal

Build a validator and pending-label agreement summary for the NL4OPT external rater sheets, including disagreement and adjudication scaffolds.

## User Value

The NL4OPT external packets are ready for two independent human raters. Before
labels are collected, the project needs a reproducible analyzer that validates
the rater sheets, detects partial/invalid labels, builds the disagreement
worktable, and computes agreement metrics as soon as paired labels exist.

## Confirmed Facts

- The NL4OPT external experiment directory is
  `/Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/or-ci-external-sanity-nl4opt-2026-05-26`.
- Existing external packet artifacts include 20 `E*.md` rater packets,
  coordinator-only packet map, Rater A/B blank sheets, and a blank adjudication
  sheet.
- The 13-case and 50-case experiments already use `source_fidelity_adjudication_v2`
  label schema and agreement analyzer scripts.
- Human labels are not available yet, so the analyzer should produce
  `pending_labels` output without fabricating agreement metrics.

## Requirements

- Add a deterministic NL4OPT label-agreement analyzer script.
- Validate Rater A and Rater B CSV schemas, packet IDs, schema version, allowed
  enum values, required fields when any label is entered, and reason-category
  values.
- Validate adjudication CSV schema and prevent completed adjudication before
  both rater labels exist.
- Normalize the NL4OPT blank adjudication sheet to include `adjudicator_id`
  and `disagreement_fields`, matching the existing v2 analyzer conventions.
- Generate a disagreement worktable from completed paired labels.
- Generate JSON and Markdown summaries with completion counts, raw agreement,
  Cohen's kappa, reason-category overlap, pending packet IDs, and non-claims.
- Update the external experiment README and roadmap status so the next task is
  human labeling, not more scaffolding.

## Acceptance Criteria

- [x] `build_nl4opt_label_agreement.py` exists and supports `--check`.
- [x] Running the analyzer writes:
      `external-sanity-nl4opt-disagreement-worktable-v2-2026-05-26.csv`,
      `external-sanity-nl4opt-label-agreement-summary-v2-2026-05-26.json`,
      and `external-sanity-nl4opt-label-agreement-summary-v2-2026-05-26.md`.
- [x] The current summary status is `pending_labels`, with 20 packets, 0 paired
      complete, and 20 pending packet IDs.
- [x] The analyzer check validates the current blank rater/adjudication sheets
      without error.
- [x] `uv run python build_nl4opt_label_agreement.py --check` passes.
- [x] `uv run python -m py_compile build_nl4opt_label_agreement.py` passes.
- [x] `uv run python build_nl4opt_blinded_rater_packets.py --check` still
      passes after adjudication-sheet normalization.
- [x] `git diff --check` passes in the notes repo.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
