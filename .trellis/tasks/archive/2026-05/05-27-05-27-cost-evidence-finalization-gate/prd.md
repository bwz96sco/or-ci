# Cost evidence finalization gate

## Goal

Add a deterministic cost/throughput finalization gate for report output so observed machine usage stays separated from missing billing, latency, human-time, and accepted-artifact-denominator evidence.

## Requirements

- Add a notes-side cost evidence finalization gate for the paper evidence pack.
- The gate must read the existing 50-case cost/throughput ledger and preserve
  its partial-status semantics.
- Create an operator-editable cost evidence input CSV with explicit rows for:
  - billing basis policy;
  - price card or billing export;
  - latency source policy;
  - human labeling minutes;
  - human adjudication minutes;
  - accepted-artifact denominator.
- The gate must generate JSON and Markdown readiness artifacts that separate:
  - observed machine usage already supported by the 50-case ledger;
  - missing inputs required before dollar, latency, human-time, or
    cost-per-accepted-artifact claims.
- `--check` must validate the input CSV schema/order, reject invalid
  "recorded" rows without source/provenance fields, and verify generated JSON
  and Markdown are fresh.
- `--self-test` must exercise pending, invalid-recorded, and complete-recorded
  input states without touching project files.
- Wire the finalization gate into paper evidence-pack readiness so the cost
  row cites the gate artifact instead of relying only on prose blockers.
- Wire the finalization gate into the evidence-gate smoke report.
- Preserve all non-claim rules: do not invent billing rates, latency, human
  minutes, denominators, labels, accepted artifacts, or report-ready claims.

## Acceptance Criteria

- [x] `build_cost_evidence_finalization_gate.py` exists.
- [x] Cost evidence input CSV, JSON, and Markdown artifacts exist.
- [x] The gate reports a blocked/incomplete status while billing, latency,
      human-time, and denominator rows are not recorded.
- [x] `--check` passes.
- [x] `--self-test` passes.
- [x] Paper evidence-pack readiness cites the cost finalization gate and still
      reports `report_ready=false`.
- [x] Evidence-gate smoke includes the cost finalization gate and still passes
      with `report_ready=false`.
- [x] Existing cost ledger, intake, receipt, paper-readiness,
      execution-board, and project tests still pass.
- [x] No cost dollars, latency seconds, human minutes, accepted-artifact
      denominator, labels, adjudication, mutation outcome, external-label
      claim, or report-ready claim is created.

## Notes

- This is a report-output gate, not a pricing model.
