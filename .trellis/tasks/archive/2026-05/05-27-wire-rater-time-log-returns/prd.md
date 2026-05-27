# Wire rater time-log returns

## Goal

Make human labeling time collection executable by adding explicit time-log
return artifacts to the rater-facing labeling bundles and coordinator surfaces.
The existing human-time readiness gate can only become useful if returned
packages collect a source document for human labeling minutes; this task wires
that source without inventing any minutes or changing evidence status.

## Requirements

- Add a bundle-local time-log CSV template to each human labeling bundle that
  sends cases to raters:
  - 5-case cold protocol check.
  - 13-case capstone.
  - 50-case Phase 2 BWOR pilot.
  - 20-case NL4OPT external sanity check.
- Update rater-facing README/instructions/checklists so raters return the
  completed time log alongside label sheets.
- Update distribution and coordinator send/dispatch surfaces so the time log is
  listed as an expected return source and can later be mapped into the
  operator-editable human-time evidence events CSV.
- Preserve current evidence semantics:
  - Do not record any send, return, label, time value, adjudication decision, or
    report-ready claim.
  - Keep existing intake targets and label CSV schemas stable.
  - Keep cold protocol as the critical path and capstone blocked until an
    accepted protocol-review decision.
- Regenerate affected generated artifacts and validate the existing non-mutating
  gates.

## Acceptance Criteria

- [x] Each rater bundle includes a `human-time-log.csv` or equivalent template
      with dataset/role/work-kind metadata and blank minute/timestamp fields.
- [x] Each bundle README/instructions/checklist states that the time log must be
      returned with the completed label sheet(s).
- [x] Distribution summaries and send/dispatch packets list time-log return
      files without treating them as recorded evidence.
- [x] Human-time readiness remains pending until a coordinator maps actual
      returned time logs into the operator-editable events CSV.
- [x] Full evidence-gate smoke still passes after regeneration.
- [x] No generated label, receipt, time, mutation, baseline, or paper-ready
      status is fabricated by this task.

## Notes

- This implements the review-plan cost/throughput requirement by creating the
  provenance collection path for human labeling minutes.
