# Wire cost operator packet into paper readiness

## Goal

Connect the guarded cost-evidence operator packet into the paper-readiness and
draft report evidence chain so the cost/throughput blocker points to the
actionable final-cost input surface.

## Requirements

- Update `build_paper_evidence_pack_readiness.py` to read
  `cost-evidence-operator-packet-2026-05-27.json`.
- Add the cost operator packet to paper readiness source artifacts and gate
  snapshots.
- Include the operator packet path in the `cost_throughput_table` proof
  artifact.
- Keep the cost section blocked while the finalization gate is not ready.
- Regenerate paper readiness CSV/JSON/Markdown.
- Regenerate dependent paper draft, execution board if needed, and smoke
  artifacts.
- Preserve non-claim rules: do not record cost values, infer prices, change
  paper readiness, select a paper branch, or create human evidence.

## Acceptance Criteria

- [x] Paper readiness `--check` passes.
- [x] Paper draft `--check` passes.
- [x] Evidence-gate smoke passes and remains `report_ready=false`.
- [x] Paper readiness JSON source artifacts include `cost_operator_packet`.
- [x] `cost_throughput_table` proof includes the operator packet.
- [x] Paper draft cost section proof includes the operator packet.
- [x] Existing tests still pass.
- [x] No final-cost value, report-ready claim, or final branch decision is
      created.

## Notes

- This is proof-chain wiring only.
