# Cold protocol send packet

## Goal

Generate a copy-ready outgoing send packet for the cold-protocol rater bundle, including attachment/hash, rater message, return expectation, and receipt-event instructions without recording a send.

## Requirements

- Add a notes-side generator under
  `experiments/packs/or-ci-labeling-operations-2026-05-26/`.
- Generate JSON and Markdown send-packet artifacts for the current primary
  cold-protocol dispatch wave.
- Read existing source artifacts instead of duplicating state:
  - cold protocol dispatch brief;
  - cold protocol distribution summary;
  - human dispatch wave plan;
  - human dispatch receipt ledger;
  - human dispatch receipt-events CSV;
  - leakage audit;
  - cold intake readiness.
- Include a copy-ready rater message that names:
  - the attached ZIP;
  - the ZIP SHA-256;
  - the archive root;
  - the bundle-local instructions;
  - the bundle-local return file;
  - the packet IDs;
  - the coordinator return expectation.
- Include coordinator instructions for recording the send in
  `human-dispatch-receipt-events-2026-05-27.csv` after the package is actually
  sent.
- Validate that the current cold receipt is unsent, the receipt-events row is
  blank, the ZIP exists and matches the expected checksum, and the leakage gate
  has zero high-severity issues.
- Add `--check` mode that fails stale send-packet artifacts.
- Add `--self-test` mode that rejects unsafe source states such as a malformed
  sent receipt, non-primary cold wave, or ZIP hash mismatch.
- Wire the send-packet check/self-test into the evidence-gate smoke report.
- Preserve all no-label/no-send/no-claim constraints.

## Acceptance Criteria

- [x] `cold-protocol-send-packet-2026-05-27.json` and
      `cold-protocol-send-packet-2026-05-27.md` are generated.
- [x] The send packet includes a copy-ready rater message and exact attachment
      checksum.
- [x] The send packet includes the receipt-events row to fill after actual
      send, but does not fill it.
- [x] `build_cold_protocol_send_packet.py --check` passes.
- [x] `build_cold_protocol_send_packet.py --self-test` passes.
- [x] `build_evidence_gate_smoke_report.py --check` includes the send packet
      and passes.
- [x] Existing dispatch wave, receipt ledger, tracker, handoff, dashboard,
      paper readiness, and execution board checks still pass.
- [x] The task creates no send event, human labels, model responses, mutation
      outcomes, accepted seeds, adjudication decisions, or report-ready claims.

## Notes

- This is the last-mile operator artifact for the current cold-protocol
  dispatch. It is safe only if the receipt-events row remains blank.
