# Wire human time evidence intake

## Goal

Create a guarded, provenance-first intake surface for human labeling and
adjudication minutes so the paper cost/throughput section can later be filled
from recorded human work without hand-editing generated cost gates or
inventing values.

## Requirements

- Add an operator-editable human time event log in the notes vault for
  labeling/adjudication work.
- Generate human-time readiness JSON/CSV/Markdown artifacts from that event
  log.
- Preserve the current state when no human minutes are recorded: report-ready
  must remain false and final cost evidence must remain blocked.
- Validate recorded events strictly: unique event IDs, known evidence category,
  known work kind, positive numeric minutes, non-placeholder source reference,
  recorder identity, and ISO-8601 timestamp.
- Summarize `human_label_minutes` and `human_adjudication_minutes` separately
  for cost-evidence use, but do not write those totals into the final cost
  input CSV automatically.
- Wire the generated human-time readiness artifact into the cost operator
  packet and paper evidence readiness sources so future operators can cite it
  as the collection/check surface.
- Add non-mutating checks and self-tests to the evidence-gate smoke report.
- Do not record actual sends, returned labels, human minutes, adjudication
  outcomes, cost values, or paper-ready claims.

## Acceptance Criteria

- [x] `build_human_time_evidence_readiness.py` can generate and check
      `human-time-evidence-readiness-2026-05-27.{json,csv,md}` from an
      operator-editable `human-time-evidence-events-2026-05-27.csv`.
- [x] `build_human_time_evidence_readiness.py --self-test` rejects unsafe
      recorded-event states and proves recorded test events become ready.
- [x] The cost operator packet depends on the human-time readiness artifact for
      `human_label_minutes` and `human_adjudication_minutes`.
- [x] The paper evidence readiness gate validates the new source without
      changing `report_ready=false`.
- [x] The smoke report includes the new check and self-test and still passes.
- [x] Existing cost finalization inputs remain pending unless a real operator
      has recorded provenance-backed values.
- [x] Both repositories are clean after commits.

## Notes

- Scope is notes-vault evidence infrastructure only. It must not modify the
  OR-CI verifier package or the current external-evidence state.
