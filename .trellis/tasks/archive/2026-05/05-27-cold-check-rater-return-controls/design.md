# Cold-Check Rater Return Controls Design

## Boundary

The implementation touches only the notes-vault cold protocol bundle generator:

`experiments/or-ci-labeling-operations-2026-05-26/build_cold_protocol_rater_bundle.py`

It updates generated files under:

`cold-protocol-rater-bundle-2026-05-27/`

It does not touch label source sheets or intake state beyond regenerating the
already blank rater-facing bundle.

## New Generated Files

- `RETURN-CHECKLIST.md`: tells the rater/coordinator exactly which file to
  return, what must remain unchanged, and which intake command validates the
  returned sheet.
- `bundle-checksums.csv`: deterministic SHA-256 manifest for generated bundle
  files except itself.

The existing `bundle-summary.json` should list the new files so downstream
summaries can discover them, but existing fields must remain stable.

## Validation

The existing bundle validation already scans generated text for unsafe path and
leakage patterns. The new checklist and checksum manifest should flow through
that validation automatically as generated expected files.

Checksum generation must be deterministic: sort by in-bundle relative path and
hash UTF-8 file text.
