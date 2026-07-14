# Baseline response operator queue Design

## Boundaries

Implementation lives in the OR research notes vault:

`/Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/or-ci-self-host-exploration-2026-05-25/`

The OR-CI verifier package is not modified. The code repo only receives
Trellis task lifecycle artifacts.

## Data Flow

1. `baseline-ablation-run-queue-2026-05-26.csv` remains the authority for the
   52 expected baseline rows and frozen Extended Pro metadata.
2. `baseline-ablation-manual-submission-manifest-2026-05-27.csv` maps each row
   to the deterministic copy/paste bundle.
3. `baseline-ablation-response-intake-readiness-2026-05-27.csv` reports staged
   JSON state before promotion.
4. `baseline-ablation-response-capture-readiness-2026-05-27.csv` reports
   canonical raw-response/template state after promotion.
5. The new operator queue script joins those sources by
   `(baseline_condition, packet_id)` and emits row-level next actions.

## Current-State Contract

In the current state there are no staged, promotable, or canonical responses.
Therefore every row should direct the operator to submit the manual bundle to
ChatGPT Extended Pro and stage the returned JSON at the expected intake path.

If a future row has valid staged JSON, the next action becomes promotion. If a
future row has canonical capture complete, the next action becomes result
validation. Invalid staged/canonical/template state takes precedence over
normal next actions.

## Safety Properties

- The queue is a coordination artifact only; it never writes model responses.
- The queue does not promote staged responses or edit the response template.
- It must not infer evidence from failed Oracle attempts.
- Any model metadata mismatch remains a blocker instead of an operator action
  that could be misread as complete.

## Reporting Integration

The human handoff and paper-readiness outputs should surface the operator queue
as the baseline-response execution map. Roadmap and reconciliation notes should
continue to state that baseline evidence is pending until valid Extended Pro
responses pass intake/capture/result validation and are paired with human
labels.
