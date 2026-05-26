# Repair human labeling handoff phase2 status

## Goal

Update the human labeling handoff generator and regenerated artifacts so the 50-case pilot gate reflects completed evidence-source decisions and no longer blocks packet distribution on a stale coordinator-decision message.

## Requirements

- Update the human-labeling handoff generator so the `50-case pilot` gate row
  is derived from the completed Phase 2 evidence-source decision summary rather
  than hard-coded stale text.
- Preserve the distinction between packet distribution readiness and missing
  human labels/adjudication.
- Regenerate the human-labeling handoff Markdown and gate-summary JSON.
- Do not create or infer human labels, adjudication outcomes, model responses,
  mutation seed decisions, or baseline decisions.
- Keep the notes-roadmap state consistent: the 50-case evidence-source gate is
  complete, but source-fidelity metrics remain blocked on human labels.

## Acceptance Criteria

- [x] `human-labeling-handoff-2026-05-27.md` no longer says the 50-case
      evidence-source decision is pending.
- [x] The 50-case gate row reports 50 complete evidence-source decisions and
      keeps 75 rater rows pending / 50 adjudication rows blocked.
- [x] `build_human_labeling_handoff.py --check` passes after regeneration.
- [x] Related readiness checks still pass for 50-case decisions, labeling
      dashboard, paper evidence pack, and packet leakage.
- [x] No human labels, model responses, mutation outcomes, or baseline
      decisions are created.
- [x] Notes changes are committed; Trellis task is archived after verification.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- This is a PRD-only lightweight repair task.
