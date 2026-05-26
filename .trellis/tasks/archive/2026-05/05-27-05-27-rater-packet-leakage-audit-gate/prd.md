# Build rater packet leakage audit gate

## Goal

Add a deterministic notes-vault audit that scans rater-facing labeling packets
and human-facing handoff files for source-fidelity leakage before any
publishable human labels are collected.

The gate implements the Claude/Pro review requirement that blinding cover
packet names, headings, links, and visible paths, not only verdict columns.

## Requirements

- Scan the currently frozen rater-facing packet sets:
  - 13-case source-fidelity capstone packets.
  - 50-case Phase 2 source-fidelity packets.
  - NL4OPT external sanity-check packets.
  - Cold-check human-labeling handoff files.
- Flag banned rater-facing leakage terms, including agent verdicts,
  source-fidelity reviewer decisions, prior accepted/rejected/provisional
  state, coordinator-only maps, and raw evidence-root paths.
- Keep coordinator-only maps and internal manifests out of the rater-facing
  pass/fail denominator while still reporting their presence as trusted
  coordinator artifacts.
- Emit CSV, JSON, and Markdown readiness artifacts with counts by packet set,
  severity, and issue type.
- Provide `--check` validation so stale or failing audit artifacts are caught.
- Provide a self-test proving the detector rejects obvious leakage strings.
- Update roadmap/reconciliation/handoff notes to point to the leakage audit.
- Do not alter, regenerate, or fill any human labels.
- Do not infer source-fidelity metrics, false-accept rates, or baseline
  decisions from the audit.

## Acceptance Criteria

- [x] Audit script runs with `uv run python`.
- [x] Current audit reports all scanned packet sets and their issue counts.
- [x] Any high-severity leak makes `--check` fail.
- [x] Self-test proves verdict/status/path leakage is detected.
- [x] Roadmap/reconciliation/handoff notes reference the leakage audit gate.
- [x] Existing human-labeling, 50-case, NL4OPT, and baseline validators still pass.
- [x] Notes repo is clean after commit.
- [x] Trellis task is archived after verification.

## Notes

- This is an evidence-readiness gate. It may identify packet leakage that must
  be fixed in a later packet-redaction task; it must not silently rewrite
  rater-facing evidence.
