# Design: Acceptance-Layer Replay For Material Mutants

## Boundary

Implementation lives in the OR-research experiment pack:

`/Users/zhangbowen/Projects/OR/note/OR-research/experiments/constructed-source-fidelity-fault-benchmark-2026-06-10/`

OR-CI package code remains unchanged. The replay consumes already-generated
OR-CI mutant reports from `materiality_ledger.csv`; it does not rerun model
generation or solver verification unless a later repair requires it.

## Data Flow

```text
materiality_ledger.csv
  -> run_acceptance_layer_replay.py
  -> acceptance_layer_replay_ledger.*
  -> acceptance_layer_summary.*
  -> acceptance_layer_execution_log.md
  -> results_ledger.csv / result_audit.md / claim_ledger.csv / claim_update.md
```

## Denominator Contract

Primary false-accept denominators include only rows where:

- `denominator_bucket == material_valid`
- materiality was established by the previous original-mutant solve comparator

Rows marked `silent_or_equivalent` or `solver_error_or_invalid_mutant` stay
visible in prior ledgers but do not count as detector misses or accepts in this
task.

## Layer Semantics

### `execution_only`

Accepts if the mutant report has an optimal original solver status. This layer
models "the code ran and solved" without checking semantic invariants or source
fidelity.

### `answer_only_mutant_reference`

Accepts if the mutant report has a numeric optimal objective. This is answer
checking against the provided mutant ProblemSpec reference result. It does not
compare against the original-source answer because that would be a hidden
source-fidelity oracle, not answer-only validation.

### `or_ci_verifier_only`

Accepts if `or_ci_status == PASS` and `or_ci_classification == SUCCESS`.

### `source_fidelity_oracle`

Rejects every `material_valid` constructed mutant because materiality plus
mutation metadata proves the artifact no longer matches the original source.
This is the deterministic capstone source-fidelity layer for the pilot, not an
LLM judge.

### `layered_or_ci_plus_source_fidelity`

Accepts only if both OR-CI and the source-fidelity oracle accept. For material
constructed mutants, this should reject all rows.

## Output Contracts

`acceptance_layer_replay_ledger.csv` has one row per material-valid mutant per
layer, including:

- mutation id, seed case id, fault family;
- layer id;
- accept/reject decision;
- false-accept flag;
- detector evidence path;
- decision rationale;
- denominator inclusion status.

`acceptance_layer_summary.csv` aggregates by layer and by layer/fault-family:

- denominator count;
- accepted count;
- rejected count;
- false-accept count;
- detection count;
- false-accept rate;
- detection rate.

Markdown and JSON siblings summarize the same data for paper-planning and
inspection.

The standard research-experiment files remain valid and are updated with a new
acceptance-layer claim while preserving the previous materiality claim.

## Metadata-Leak Policy

The execution, answer-only, and OR-CI decisions may read only solver/report
fields from `materiality_ledger.csv` and referenced report JSON. The
`source_fidelity_oracle` layer is the only layer allowed to use the constructed
materiality label as ground truth.

## Tradeoffs

This task does not call LLM judges. That keeps the next result cheap,
deterministic, and unblocked by external accounts while still producing the
core evidence table needed to decide whether LLM/full-layer variants are worth
running.

## Rollback

All generated files are confined to the experiment pack. Regeneration should be
idempotent: rerunning `run_acceptance_layer_replay.py` rewrites only
acceptance-layer outputs and standard Stage 05/06 summary files.
