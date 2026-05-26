# Design

## Boundary

This is a notes-evidence capture task, not an OR-CI verifier code change. The
code repository only owns Trellis task bookkeeping. Experiment artifacts live
in `/Users/zhangbowen/Projects/OR/note/OR-research`.

## Data Flow

1. Read one manual submission bundle for each target row.
2. Submit the bundle to Oracle CLI browser mode with Pro selected and extended
   thinking time requested.
3. Save the final assistant response as an immutable attempt output.
4. Parse the attempt output as JSON and add only the required staged metadata:
   `run_id`, `model_or_tool`, and `model_version`.
5. Stage the JSON under `baseline-ablation-response-intake-2026-05-27/`.
6. Promote one valid row at a time with `build_baseline_response_intake.py
   --promote`.
7. Regenerate downstream readiness artifacts.

## Promotion Contract

Promotion is delegated to the existing intake script. A response is promotable
only when the script validates condition, packet id, allowed enum values,
required metadata, expected model labels, and pending response-template state.

## Non-Claims

Captured baseline responses are model-run bookkeeping only. They do not support
baseline performance, false-accept, accuracy, source-fidelity, or paper-branch
claims until paired with adjudicated human labels.
