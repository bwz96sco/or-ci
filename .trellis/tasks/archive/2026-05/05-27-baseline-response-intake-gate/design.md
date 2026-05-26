# Build baseline response intake gate Design

## Boundaries

The implementation lives in the notes vault experiment directory:

`/Users/zhangbowen/Projects/OR/note/OR-research/experiments/or-ci-self-host-exploration-2026-05-25/`

It must not modify OR-CI verifier package code. Trellis artifacts in this repo
record the task lifecycle only.

## Data Flow

1. `baseline-ablation-run-queue-2026-05-26.csv` defines the 52 expected
   baseline rows, expected raw-response path, and frozen Extended Pro metadata.
2. Operators paste returned JSON into a staging directory instead of directly
   editing canonical response artifacts.
3. The new intake script scans staged JSON files and emits readiness CSV/JSON/MD
   with statuses such as pending, valid staged, invalid staged, already
   promoted, or promotion blocked.
4. An explicit promote command validates one row again, writes the JSON to the
   canonical raw-response path, and updates only that row in
   `baseline-ablation-response-template-2026-05-26.csv`.
5. Existing validators remain authoritative for canonical evidence:
   `build_baseline_response_capture.py` and
   `build_baseline_ablation_results.py`.

## Contracts

Staged JSON must be a single JSON object matching the baseline output schema
and must include exact queue metadata:

- `baseline_condition`
- `packet_id`
- `model_or_tool`
- `model_version`
- decision fields already required by existing validators

The staged metadata must exactly match the queue's `ledger_model_or_tool` and
`ledger_model_version`. Instant, ordinary Pro, transcript text, malformed JSON,
or any other model label remains invalid.

## Safety Properties

- Generation and check modes are read-only against canonical response artifacts.
- Promotion is opt-in and row-scoped.
- Promotion refuses invalid staged data and refuses to overwrite an existing
  canonical raw response unless an explicit future option is added. This task
  does not need overwrite support.
- The script records readiness only; it does not infer a model response from
  failed Oracle attempt logs.

## Reporting Integration

Roadmap and report-readiness notes should describe the intake gate as a
staging/promotion safeguard. They must continue to state that baseline evidence
is pending until 52 valid raw responses and adjudicated human labels exist.
