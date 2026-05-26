# Cold-check rater return controls

## Goal

Harden the five-packet cold protocol rater bundle so a human rater can receive
it, fill the correct sheet, and return it through the staged intake gate with
less coordinator ambiguity.

## Requirements

- Extend the existing cold protocol rater bundle generator in the notes vault.
- Add a deterministic return checklist inside
  `cold-protocol-rater-bundle-2026-05-27/`.
- Add a deterministic checksum manifest for rater-facing bundle files.
- Regenerate the cold protocol rater bundle so the new files are included.
- Preserve existing safety rules:
  - no coordinator maps;
  - no source notes-vault paths;
  - no raw artifact roots;
  - no prior verdicts or source-fidelity review notes;
  - no human labels created or inferred.
- Keep existing bundle validators and downstream handoff/readiness checks
  passing.

## Acceptance Criteria

- [ ] `build_cold_protocol_rater_bundle.py` writes a return checklist and
      checksum manifest.
- [ ] The checksum manifest covers all rater-facing bundle files except the
      checksum file itself.
- [ ] `uv run python build_cold_protocol_rater_bundle.py --check` passes.
- [ ] Cold intake, human handoff, leakage audit, paper readiness, and
      next-stage execution board checks still pass.
- [ ] No labels, adjudication rows, model responses, mutation outcomes, or
      paper claims are created.

## Notes

- This is critical-path support for the 5-case cold protocol check, not a
  substitute for the human rater.
