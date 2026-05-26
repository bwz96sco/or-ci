# Source Fidelity Labeling Calibration Design

## Boundaries

- OR-CI verifier code remains untouched.
- OR-LLM-Agent product code remains untouched.
- The durable deliverables live in the OR research note repo under the existing
  self-host exploration experiment directory.
- The helper script is report-build tooling for this experiment, not a product
  CLI.

## Data Flow

1. Read `source-fidelity-rubric-capstone-2026-05-26.json`.
2. Extract `baseline_cases` and `clarified_cases`.
3. Write one adjudication-sheet row per case.
4. Leave human label columns blank.
5. Read the sheet back and write calibration JSON/Markdown:
   - `pending_labels` when required human labels are missing.
   - agreement and false-accept metrics when labels are present.

## CSV Contract

Rows use `case_key` as the unique key. Baseline rows use `BWOR-001`; clarified
rows use `BWOR-014/attempt-1`.

Required human fields are:

- `human_capability_status`
- `human_source_fidelity_status`
- `human_materiality`
- `human_final_acceptance`
- `human_reason_primary`
- `human_confidence`
- `adjudicator`
- `adjudicated_at`

Blank required human fields mean calibration is not ready.

## Calibration Rules

- Agent accepted means `agent_fidelity_status == "llm_accepted"`.
- Human accepted means `human_source_fidelity_status == "accepted"` and
  `human_final_acceptance == "accepted"`.
- A material false accept is an agent-accepted case whose human source fidelity
  is rejected and whose human materiality is `material` or `unresolved`.
- Pending rows are not silently excluded; the report must show the pending
  count and `calibration_status=pending_labels`.

## Compatibility

The sheet extends the existing 50-case adjudication vocabulary with capstone
specific fields. Existing labels remain readable because the vocabulary is
unchanged.
