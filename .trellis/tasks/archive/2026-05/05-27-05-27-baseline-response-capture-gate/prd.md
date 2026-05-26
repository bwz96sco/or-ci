# Build baseline response capture gate

## Goal

Add a scan/readiness gate for the 52 baseline-ablation raw-response JSON paths
without creating model responses or filling baseline decisions.

## Requirements

- Read the deterministic baseline run queue.
- Check every expected raw response JSON path.
- Validate any present raw response JSON against the output schema fields used
  by `build_baseline_ablation_results.py`.
- Detect orphan raw response files outside the run queue.
- Cross-check the response template so raw files, response metadata, and
  completed decisions cannot drift silently.
- Generate CSV/JSON/Markdown readiness artifacts.
- Include explicit non-claims:
  - no model responses are created;
  - no response-template rows are filled;
  - no baseline decisions, FAR metrics, or source-fidelity claims are inferred.
- Add `--check` validation and a self-test that proves malformed response JSON
  is rejected.

## Acceptance Criteria

- [x] Builder script runs with `uv run python`.
- [x] Current readiness reports 52 expected responses, 0 raw responses present,
      and 0 completed response-template rows.
- [x] Orphan response files and malformed JSON would fail validation.
- [x] Existing baseline run-package/results/manual-submission checks still pass.
- [x] Roadmap/integration/reconciliation notes reference the response capture gate.
- [x] Notes repo is clean after commit.
- [x] Trellis task is archived after verification.

## Out of Scope

- Submitting prompts to Oracle/ChatGPT.
- Creating raw response JSON files.
- Editing the response template with model outputs.
- Parsing model responses into final paper metrics.
- Computing false-accept rates.
