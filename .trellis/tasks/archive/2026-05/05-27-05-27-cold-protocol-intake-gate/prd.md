# Build cold protocol intake gate

## Goal

Add a deterministic notes-vault gate for the five-packet cold protocol check.
The gate validates the cold-rater sheet, reports whether the protocol-debug
step is still pending or ready for review, and prevents cold-check labels from
being treated as evaluation/reliability evidence.

## Requirements

- Read the existing cold-check handoff CSV and blank cold-check label sheet.
- Validate that the handoff packet set and label-sheet packet set match exactly.
- Validate any filled cold-check label row against the v2 source-fidelity label
  schema.
- Reject partial label rows: if any label field is filled, all required cold
  label fields must be filled.
- Emit CSV, JSON, and Markdown readiness artifacts with per-packet state.
- Report global status as pending, partial/invalid, or complete-for-protocol
  review.
- Include explicit non-claims that cold-check labels are training/debug only
  and must be relabeled under the final frozen protocol before evaluation use.
- Provide `--check` validation and a self-test for partial row rejection.
- Wire the gate into the human-labeling handoff and roadmap/reconciliation
  notes.
- Do not create, modify, or infer any human label values.

## Acceptance Criteria

- [x] Intake script runs with `uv run python`.
- [x] Current readiness reports 5 expected cold-check packets and 0 completed
      cold labels.
- [x] Partial cold-label rows fail validation.
- [x] The human-labeling handoff references the intake gate.
- [x] Roadmap/reconciliation notes reference the intake gate.
- [x] Existing labeling, leakage, packet, and baseline validators still pass.
- [x] Notes repo is clean after commit.
- [x] Trellis task is archived after verification.

## Notes

- This is an intake/readiness gate only. It should not compute reliability
  claims from the five-packet cold check.
