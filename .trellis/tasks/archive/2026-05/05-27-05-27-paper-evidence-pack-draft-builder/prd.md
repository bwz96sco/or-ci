# Guarded paper evidence pack draft builder

## Goal

Generate a guarded draft paper evidence pack from current readiness gates, blockers, proof artifacts, and branch precommitments without creating final claims while report_ready remains false.

## Requirements

- Add a notes-side builder under
  `experiments/or-ci-paper-evidence-pack-2026-05-27/`.
- Generate guarded draft paper evidence-pack JSON and Markdown artifacts from
  the current paper readiness CSV/JSON and execution board JSON.
- The draft must include:
  - status and `report_ready` from paper readiness;
  - every report-table section from readiness, with status, proof artifact,
    missing evidence, allowed claim, forbidden claims, and verification gate;
  - current critical next action from the execution board;
  - required evidence blockers;
  - forbidden-claim checklist;
  - precommitted Branch A/Branch B headline options, both blocked until the
    final branch decision gate is ready.
- The builder must refuse to emit a final-ready draft while required evidence
  blockers remain.
- The Markdown must read as a draft/report skeleton, not a completed paper
  result. Blocked sections must clearly say they are placeholders.
- Add `--check` to verify generated draft artifacts are fresh.
- Add `--self-test` to exercise blocked and ready synthetic states without
  touching project files.
- Wire the draft builder into the evidence-gate smoke report.
- Preserve all non-claim rules: do not create or infer labels, model results,
  mutation results, external accuracy, cost dollars, final branch choice, or
  report-ready claims.

## Acceptance Criteria

- [x] `build_paper_evidence_pack_draft.py` exists.
- [x] `paper-evidence-pack-draft-2026-05-27.json` and `.md` exist.
- [x] The generated draft includes all 16 readiness sections.
- [x] The draft status is blocked/non-final while readiness has blockers.
- [x] Branch A and Branch B are both present and explicitly blocked.
- [x] `--check` passes.
- [x] `--self-test` passes.
- [x] Evidence-gate smoke includes the draft builder and still passes with
      `report_ready=false`.
- [x] Existing readiness, execution-board, smoke, and project tests still pass.
- [x] No label, adjudication, mutation outcome, external-label claim,
      cost-dollar claim, final branch decision, or report-ready claim is
      created.

## Notes

- This is a report skeleton generator, not a final paper generator.
