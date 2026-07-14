# Cold-Check Distribution Package Design

## Boundary

Implementation stays inside the notes vault:

`experiments/packs/or-ci-labeling-operations-2026-05-26/`

It reads the already-generated `cold-protocol-rater-bundle-2026-05-27/`
directory and creates a derived ZIP plus summaries. It does not modify source
labels, packet contents, intake state, or paper claims.

## Outputs

- `cold-protocol-rater-bundle-2026-05-27.zip`
- `cold-protocol-rater-bundle-distribution-2026-05-27.json`
- `cold-protocol-rater-bundle-distribution-2026-05-27.md`

The ZIP should contain files under the top-level directory
`cold-protocol-rater-bundle-2026-05-27/` so extraction is safe and obvious.

## Determinism

Use Python `zipfile` with fixed timestamps and sorted relative paths. Hash the
resulting archive bytes with SHA-256 and record the checksum in JSON/Markdown.

## Validation

`--check` recomputes the expected ZIP bytes, JSON summary, and Markdown summary
from the current bundle and compares them against disk. It also verifies the ZIP
entries match the current safe bundle files exactly.
