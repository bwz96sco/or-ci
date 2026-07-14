# Cost evidence operator packet

## Goal

Generate a guarded operator packet for the six missing final cost-evidence
inputs so the paper cost/throughput table can move from blocked to
provenance-backed when external billing, latency, and human-time evidence
exists.

## Requirements

- Add a notes-side builder under
  `experiments/packs/or-ci-paper-evidence-pack-2026-05-27/`.
- Generate deterministic JSON and Markdown artifacts named
  `cost-evidence-operator-packet-2026-05-27.*`.
- Read the existing cost finalization gate JSON, cost finalization input CSV,
  paper readiness JSON, and human evidence tracker JSON.
- For each expected cost input, render:
  - current status;
  - why it is required;
  - required fields for a recorded row;
  - allowed source/provenance examples;
  - forbidden claims while pending;
  - exact CSV row update template.
- Include the observed machine-throughput summary from the finalization gate.
- Include the current dependency status for human-label minutes,
  adjudication minutes, and accepted-artifact denominator.
- Add `--check` to verify generated artifacts are fresh.
- Add `--self-test` covering pending, partially filled invalid, and fully
  recorded synthetic rows.
- Wire the packet into the evidence-gate smoke report.
- Preserve non-claim rules: do not invent prices, billing exports, latency,
  human minutes, accepted-artifact denominators, final costs, report-ready
  status, or paper branch decisions.

## Acceptance Criteria

- [x] `build_cost_evidence_operator_packet.py` exists.
- [x] `cost-evidence-operator-packet-2026-05-27.json` and `.md` exist.
- [x] The packet includes all six cost-evidence inputs.
- [x] The packet includes observed machine-throughput evidence but keeps
      final cost evidence blocked.
- [x] The packet includes CSV update templates for recorded rows.
- [x] `--check` passes.
- [x] `--self-test` passes.
- [x] Evidence-gate smoke includes the packet and remains `report_ready=false`.
- [x] Existing tests still pass.
- [x] No cost dollars, latency seconds, human-time value, accepted-artifact
      denominator, report-ready claim, or final branch decision is created.

## Notes

- This is an operator guidance packet, not a cost calculator.
