# Build baseline response intake gate

## Goal

Add a guarded staging/intake gate for the 52 baseline-ablation model
responses in the notes vault. The gate must let operators place returned JSON
responses in a staging directory, validate them against the frozen Extended
Pro run queue and output schema, and promote only valid staged responses into
the canonical raw-response/template artifacts through an explicit command.

This moves the OR-CI research roadmap forward on the baseline evidence track
without creating, inferring, or accepting any model response that is not
actually present and policy-valid.

## Requirements

- Work in the notes vault under
  `experiments/packs/or-ci-self-host-exploration-2026-05-25/`.
- Reuse the existing baseline queue, output schema, manual bundle manifest,
  raw-response directory, response template, response capture readiness, and
  ablation result validators.
- Add a staging/intake script and generated readiness artifacts that report
  one row per expected baseline response.
- Default generation and `--check` must be read-only with respect to canonical
  raw-response JSON files and `baseline-ablation-response-template-2026-05-26.csv`.
- A promotion path must require an explicit command and row selector, refuse
  promotion unless the staged JSON validates, and preserve exact frozen
  `model_or_tool` / `model_version` metadata from the run queue.
- The intake validator must reject malformed JSON, orphan staged files,
  condition/packet mismatches, model metadata mismatches, invalid decision
  fields, and attempts to treat failed Oracle transcript outputs as accepted
  raw responses.
- Generated summaries must keep the current non-claims: no baseline decision,
  false-accept rate, source-fidelity accuracy, or paper branch decision exists
  until validated model responses are paired with adjudicated human labels.
- Wire the new readiness state into the active roadmap/reconciliation/report
  scaffolds so the next human/model-run task is clear.

## Acceptance Criteria

- [x] A new baseline response intake script exists in the experiment folder.
- [x] Running the script without promotion writes deterministic CSV/JSON/MD
      readiness artifacts and does not create canonical raw-response JSON files
      or edit the canonical response template.
- [x] `--check` verifies the readiness artifacts are current.
- [x] `--self-test` proves malformed JSON and model-policy mismatch rejection.
- [x] An explicit promote command refuses currently pending rows and leaves the
      canonical raw-response/template artifacts unchanged.
- [x] Existing baseline validators still pass:
      `build_baseline_response_capture.py --check` and
      `build_baseline_ablation_results.py --check`.
- [x] Paper/readiness notes mention the staged intake gate while keeping
      `report_ready=false`.
- [x] No human labels, model responses, mutation outcomes, or accuracy/FAR
      claims are fabricated.

## Notes

- This is an automation-support task. It does not resolve the human-labeling
  blocker or complete the baseline evidence track by itself.
