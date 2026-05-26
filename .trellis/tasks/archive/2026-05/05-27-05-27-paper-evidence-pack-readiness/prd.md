# Build paper evidence pack readiness scaffold

## Goal

Add a deterministic notes-vault report scaffold that aggregates the current
OR-CI next-stage gates into a paper evidence-pack readiness view.

The scaffold must make the final report output shape concrete while preserving
the current non-claims: no human-label metrics, false-accept rates, baseline
performance, mutation recall, or external accuracy claims may be inferred from
pending evidence.

## Requirements

- Read existing machine-readable gate artifacts for:
  - cold protocol intake;
  - rater packet leakage;
  - human labeling operations/handoff;
  - 13-case capstone label agreement;
  - 50-case evidence-source decision and label agreement;
  - baseline response capture/comparison readiness;
  - mutation seed review/work queue readiness;
  - NL4OPT external label agreement;
  - 50-case cost/throughput ledger when available.
- Emit JSON, CSV, and Markdown readiness artifacts under the notes vault.
- Include a report-table checklist covering the capstone agreement table,
  50-case pilot table, baseline confusion matrices, mutation per-family table,
  NL4OPT external sanity-check table, and cost/throughput table.
- For each table, record status, proof artifact, missing evidence, and allowed
  claim.
- Compute an overall status that remains blocked/pending until human labels,
  baseline responses, mutation accepted seeds/results, and external labels are
  available.
- Include explicit forbidden-claim checks so the scaffold cannot be mistaken
  for a final paper evidence pack.
- Provide `--check` validation and a self-test that proves incomplete human
  evidence cannot become report-ready.
- Update roadmap/reconciliation notes to reference the scaffold.
- Do not edit human labels, baseline response templates, mutation seed reviews,
  or evidence-source decisions.

## Acceptance Criteria

- [x] Builder runs with `uv run python`.
- [x] Current readiness marks final report evidence as pending/blocked, not
      complete.
- [x] Checklist includes every report capstone section named in the roadmap.
- [x] Self-test proves missing human labels block report-ready status.
- [x] Roadmap/reconciliation notes reference the evidence-pack readiness
      scaffold.
- [x] Existing labeling, baseline, mutation, packet, and external validators
      still pass.
- [x] Notes repo is clean after commit.
- [x] Trellis task is archived after verification.

## Notes

- This is a scaffold/readiness artifact, not the final paper evidence pack.
