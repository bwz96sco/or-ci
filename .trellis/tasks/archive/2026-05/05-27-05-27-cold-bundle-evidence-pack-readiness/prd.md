# Wire cold rater bundle into evidence pack

## Goal

Update the paper evidence-pack readiness builder and generated artifacts so they record the cold protocol rater bundle as ready for human distribution while keeping cold labels and evaluation claims blocked.

## Requirements

- Update the paper evidence-pack readiness builder so it reads the cold
  protocol rater bundle summary created by the labeling operations track.
- Add bundle status/count information to the gate snapshot or table text so
  coordinators can see the cold-check package is ready for human distribution.
- Preserve the existing evidence blocker: no cold-check labels have been
  collected, and no reliability/evaluation claim is allowed from the bundle
  alone.
- Regenerate readiness Markdown/JSON/CSV artifacts.
- Do not create or infer human labels, adjudication outcomes, model responses,
  mutation outcomes, or baseline decisions.

## Acceptance Criteria

- [x] Paper evidence-pack readiness reports the cold rater bundle status as
      ready for distribution.
- [x] Paper evidence-pack readiness still reports `pending_required_evidence`
      and `report_ready=false`.
- [x] `build_paper_evidence_pack_readiness.py --check` passes.
- [x] Cold bundle, handoff, intake, and leakage checks still pass.
- [x] No human labels, model responses, mutation outcomes, or baseline
      decisions are created.
- [x] Notes changes are committed; Trellis task is archived after verification.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- This is a PRD-only lightweight readiness-wiring task.
