# Design: Human Dispatch Wave Plan

## Boundary

The builder belongs in:

`/Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/or-ci-labeling-operations-2026-05-26/`

It is an operations artifact that reads generated readiness state and writes a
dispatch plan. It must not mutate label sheets, promote labels, accept seeds,
or send anything externally.

## Source Inputs

- `human-evidence-collection-tracker-2026-05-27.json`
- `labeling-operations-summary-2026-05-26.json`
- `paper-evidence-pack-readiness-2026-05-27.json`
- `next-stage-execution-board-2026-05-27.json`

The evidence-gate smoke runner consumes this wave plan through its own
`--check` command. The wave-plan builder must not read the smoke report, or the
two artifacts become mutually stale.

## Output Contract

`human-dispatch-wave-plan-2026-05-27.json` contains:

- `status`
- `primary_wave_id`
- `primary_next_track`
- `primary_next_action`
- `ready_parallel_tracks`
- `blocked_tracks`
- `paper_report_ready`
- `pending_direct_human_assignments`
- `waves[]`
- `non_claims[]`

Each wave row contains:

- `wave_id`
- `wave_order`
- `track_id`
- `wave_class`
- `send_state`
- `current_status`
- `operator_state`
- `next_operator_action`
- `expected_count`
- `completed_count`
- `progress`
- `sendable_package`
- `sendable_package_sha256`
- `dispatch_artifact`
- `return_or_staging_target`
- `validation_command`
- `blocker`
- `gate_to_open`
- `non_claim_guardrail`

## Validation Rules

- Exactly one tracker row must match `primary_next_track`.
- All `ready_parallel_tracks` must exist in tracker rows.
- All `blocked_tracks` must exist in tracker rows.
- `paper_report_ready` must stay false unless both paper readiness and board
  readiness are true.
- Source files referenced by tracker rows must exist where appropriate:
  package, dispatch artifact, return/staging parent, and validation command
  script.

## Wave Classification

- `send_primary_now`: `track_id == primary_next_track`
- `send_parallel_when_raters_available`: track in `ready_parallel_tracks`
- `blocked_wait_for_prior_gate`: track in `blocked_tracks`
- `hold_report_output`: synthetic report row that reminds operators not to
  advance paper output while evidence is missing

## Failure Mode

`--check` compares generated JSON/Markdown with committed files and fails on
source inconsistency. A stale plan means an operator might send a blocked bundle
or miss a newly unblocked wave.
