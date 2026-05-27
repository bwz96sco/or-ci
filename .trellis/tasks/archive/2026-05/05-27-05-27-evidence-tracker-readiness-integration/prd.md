# Integrate Human Evidence Tracker Into Readiness Surfaces

## Goal

Make the generated human evidence collection tracker an explicit source for
the next-stage execution board, human labeling handoff, and paper evidence-pack
readiness gate.

## Requirements

- The execution board builder must require the tracker JSON and expose it in
  source artifacts and proof chains.
- The human labeling handoff builder must include tracker CSV/JSON/Markdown in
  generated files and show the tracker as the compact operator control sheet.
- The paper evidence-pack readiness builder must require the tracker JSON/MD,
  validate its critical invariants, and include tracker status in the gate
  snapshot.
- Generated board, handoff, and readiness Markdown/JSON must reference the
  tracker.
- Preserve evidence state:
  - cold check remains 0/5;
  - capstone remains blocked behind cold protocol check;
  - Phase 2 and NL4OPT remain label-pending;
  - mutation seed review remains 0 accepted seeds and 0 run-eligible rows;
  - label promotion remains 0 ready datasets;
  - paper readiness remains `report_ready=false`.

## Acceptance Criteria

- [x] `build_human_evidence_collection_tracker.py --check` passes.
- [x] `build_next_stage_execution_board.py --check` passes and source artifacts
      include the tracker.
- [x] `build_human_labeling_handoff.py --check` passes and generated handoff
      lists the tracker.
- [x] `build_paper_evidence_pack_readiness.py --check` passes and its gate
      snapshot includes tracker status/primary next action.
- [x] Generated JSON asserts the tracker primary action is the cold check and
      `paper_report_ready=false`.
- [x] Existing distribution, leakage, promotion, and mutation seed-review
      checks still pass.
- [x] Notes changes and Trellis archive are committed.

## Out Of Scope

- Do not collect labels, edit staged return CSVs, promote labels, accept
  mutation seeds, regenerate packet ZIPs, or change baseline responses.
