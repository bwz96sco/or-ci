# Build cold protocol rater bundle

## Goal

Create and validate a rater-facing distribution bundle for the five cold protocol check packets so the next human-labeling step can proceed without exposing coordinator-only maps or evidence paths.

## Requirements

- Add a deterministic notes-vault builder for the five-packet cold protocol
  rater distribution bundle.
- Build the bundle only from the existing cold-check handoff CSV and blank
  cold-check label CSV.
- Copy only rater-facing packet files and the blank rater label sheet into the
  bundle. Do not copy coordinator-only maps, raw evidence roots, model
  responses, adjudication sheets, or analysis outputs.
- Produce a bundle manifest/readme/check artifact that lets a coordinator
  verify exactly what may be sent to a human cold rater.
- Keep the existing cold protocol intake and leakage audits authoritative; this
  task must not create or infer human labels.

## Acceptance Criteria

- [x] `build_cold_protocol_rater_bundle.py --check` passes.
- [x] The generated bundle contains exactly five packet Markdown files and one
      blank cold-check label CSV.
- [x] Bundle manifest lists only rater-facing paths inside the bundle, not
      original artifact roots or coordinator maps.
- [x] Existing handoff, cold-intake, leakage-audit, and paper evidence-pack
      checks still pass.
- [x] No human labels, adjudication outcomes, model responses, mutation
      outcomes, or baseline decisions are created.
- [x] Notes changes are committed; Trellis task is archived after verification.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- This is a PRD-only lightweight support task.
