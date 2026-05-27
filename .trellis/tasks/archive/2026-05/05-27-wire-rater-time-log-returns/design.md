# Design: Wire rater time-log returns

## Current Gap

`build_human_time_evidence_readiness.py` already checks the operator-editable
human-time events CSV, and the paper/cost readiness gates are blocked on human
labeling and adjudication minutes. The rater-facing bundles currently focus on
label CSVs, so the coordinator has no standard returned source file to cite
when later filling human-time evidence events.

## Approach

Add a generated bundle-local `human-time-log.csv` template to each rater bundle.
The template is intentionally separate from the canonical
`human-time-evidence-events-2026-05-27.csv` because raters should not need to
know wave IDs or paper evidence schema details. The coordinator can later map a
returned time log into the canonical event log with a source reference and
receipt metadata.

Template fields:

- `dataset_id`
- `participant_role`
- `participant_id`
- `work_kind`
- `minutes`
- `started_at`
- `completed_at`
- `notes`

Defaults:

- `dataset_id`: one of `cold_protocol_check`, `capstone_13`, `phase2_50case`,
  or `nl4opt_external`.
- `participant_role`: `rater_a`, `rater_b`, or `cold_protocol_rater`.
- `work_kind`: `protocol_debug_labeling`, `initial_labeling`, or
  `external_labeling`.
- `minutes`, timestamps, and notes remain blank for the external rater to fill.

## Files To Touch

Notes-vault generators under
`experiments/or-ci-labeling-operations-2026-05-26/`:

- `build_cold_protocol_rater_bundle.py`
- `build_capstone_rater_bundle.py`
- `build_phase2_50case_rater_bundle.py`
- `build_nl4opt_rater_bundle.py`
- distribution/send/dispatch generators that list expected return files

Generated outputs:

- bundle directories
- distribution ZIPs/JSON/Markdown/checksums
- dispatch/send packet summaries
- downstream execution board/smoke/readiness surfaces if source hashes or
  generated summaries change

## Non-Goals

- Do not collect or invent actual minutes.
- Do not change label intake schemas.
- Do not unlock capstone distribution.
- Do not mark cost, paper, or human-time readiness complete.
- Do not modify OR-CI verifier package behavior.
