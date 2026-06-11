# NL4OPT external OR-CI adapter evidence

## Goal

Add a generic evidence-producing batch adapter path so OR-CI can consume an external research manifest, materialize linear-formulation candidates into OR-CI verifier inputs, and emit reproducible verifier ledgers for the research paper.

## Requirements

- Add a deterministic CLI path for batch evidence production from a CSV manifest.
- The manifest must support two row shapes:
  - existing OR-CI inputs: `record_id`, `statement`, `problem`, `submission`;
  - external linear formulation input: `record_id`, `statement`, `formulation`.
- The external linear formulation path must materialize:
  - an OR-CI problem metadata JSON file;
  - a generated generic `build_model(data)` submission file;
  - a source-linked evidence-pack JSON using the existing evidence-pack builder.
- The materialized OR-CI problem must use BWOR-prefixed problem ids and keep dataset-specific names as external manifest metadata, not core verifier vocabulary.
- The generated submission must build only linear continuous Gurobi models from supplied structured data.
- The adapter must support the formulation features already used by the external direct-LP audit where possible: linear objectives, linear constraints, lower/upper bounds, sum constraints, ratio constraints, and x-by-y linear relations.
- Unsupported formulation rows must be recorded in the batch ledger with a failure status instead of crashing the whole batch.
- The batch output must include:
  - per-record evidence packs;
  - materialized problem/submission files for formulation rows;
  - a CSV ledger with record id, generated problem id, status/classification, output paths, and error text when applicable;
  - a JSON summary with counts and explicit source-fidelity non-claims.
- The adapter must not:
  - parse natural-language statements into models;
  - call LLMs or network services;
  - import from `or_llm_agent`;
  - claim source-statement correctness from OR-CI `PASS`;
  - hardcode NL4OPT/NL4OR-specific behavior inside OR-CI code or tests.

## Acceptance Criteria

- [x] `uv run or-ci evidence-batch --manifest <manifest.csv> --out-dir <dir>` writes batch artifacts for valid rows.
- [x] A row with existing `problem` + `submission` inputs produces the same evidence-pack schema as `or-ci evidence-pack`.
- [x] A row with a supported linear `formulation` input materializes a valid OR-CI problem and submission, runs verification, and writes an evidence pack.
- [x] Unsupported formulation rows are represented in the ledger and summary without aborting unrelated rows.
- [x] The batch ledger is deterministic and includes enough paths/status fields for downstream research evidence ingestion.
- [x] Tests cover successful existing-input rows, successful formulation rows, and unsupported formulation rows.
- [x] `uv run pytest` passes.
- [x] No LLM/provider/network code is added.
- [x] No dataset-specific names are hardcoded in OR-CI code or tests.

## Notes

- This task is the OR-CI-side coding step for the current research R4 route.
- The concrete NL4OPT denominator remains in the OR-research manifest and ledgers; OR-CI should stay a deterministic verifier/evidence tool.
