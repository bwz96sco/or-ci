# Cold-check distribution package

## Goal

Create a deterministic distribution package for the five-packet cold protocol
rater bundle so the next human-rater step can use one sendable archive plus a
machine-checkable manifest.

## Requirements

- Add a notes-side generator under
  `experiments/packs/or-ci-labeling-operations-2026-05-26/`.
- Package the existing safe cold protocol rater bundle into a deterministic
  ZIP archive.
- Generate JSON and Markdown distribution summaries with:
  - ZIP filename;
  - ZIP SHA-256 checksum;
  - source bundle path;
  - expected file count;
  - in-archive file list;
  - non-claims and return instructions.
- Validate that the archive contains only the safe bundle's generated
  rater-facing files and no extra coordinator files.
- Wire the distribution ZIP and manifest into the human labeling handoff.
- Preserve all existing no-label/no-claim constraints.

## Acceptance Criteria

- [ ] A deterministic ZIP archive is generated for
      `cold-protocol-rater-bundle-2026-05-27/`.
- [ ] The distribution JSON and Markdown summaries are generated.
- [ ] The generator's `--check` mode passes and fails stale artifacts.
- [ ] Cold bundle, cold intake, human handoff, leakage audit, paper readiness,
      and next-stage board checks still pass.
- [ ] The change does not create or infer labels, adjudication, model
      responses, mutation outcomes, or paper claims.

## Notes

- This is a handoff/packaging artifact only.
