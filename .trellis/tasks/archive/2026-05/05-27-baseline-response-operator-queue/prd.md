# Baseline response operator queue

## Goal

Add a single operator-facing queue for the 52 baseline-ablation response rows.
The queue must join the frozen run queue, manual submission bundles, staged
response intake gate, canonical response-capture gate, and frozen Extended Pro
model-policy metadata into one auditable action list.

This advances the baseline evidence track without rerunning Oracle, creating
model responses, or accepting failed/invalid responses as evidence.

## Requirements

- Work in the notes vault under
  `experiments/or-ci-self-host-exploration-2026-05-25/`.
- Reuse the existing baseline run queue, manual submission manifest,
  response-intake readiness, response-capture readiness, response template,
  model-run policy note, and failed Oracle smoke evidence.
- Generate deterministic CSV, JSON, and Markdown artifacts that report one row
  per expected baseline response.
- Each operator row must include baseline condition, packet id, case id, manual
  bundle path, expected staged response path, expected canonical raw-response
  path, expected model/tool metadata, current intake status, current capture
  status, response-template state, next action, and blocker.
- The current no-response state must produce an explicit manual-submission
  action for all 52 rows, not a fabricated completion state.
- The queue must surface invalid/stale source states if any upstream manifest,
  readiness row, or path disagrees with the frozen run queue.
- Generated Markdown must preserve non-claims: no baseline decision, accuracy,
  false-accept rate, paper branch, or source-fidelity claim exists until valid
  Extended Pro responses are promoted and paired with adjudicated human labels.
- Wire the new operator queue into the human labeling handoff, paper evidence
  pack readiness, roadmap, and review reconciliation so the next model-run task
  points to this single queue.

## Acceptance Criteria

- [x] `build_baseline_response_operator_queue.py` exists in the self-host
      experiment directory and has normal generation plus `--check` modes.
- [x] The generated CSV/JSON/MD queue reports all 52 rows and status
      `pending_manual_baseline_responses` in the current state.
- [x] All 52 current rows have next action
      `submit_manual_bundle_to_extended_pro` and identify their manual bundle,
      staged path, canonical raw path, and exact Extended Pro metadata.
- [x] `--check` fails on stale generated queue artifacts and passes after
      generation.
- [x] Existing manual submission, response intake, response capture, human
      handoff, and paper evidence-pack readiness checks still pass.
- [x] Roadmap/reconciliation/readiness notes reference the operator queue while
      keeping baseline results and final report evidence pending.
- [x] No human labels, model responses, mutation outcomes, or accuracy/FAR
      claims are fabricated.

## Notes

- This is support automation for the baseline-response gate. It does not
  resolve the external model-run dependency or complete the baseline evidence
  track.
