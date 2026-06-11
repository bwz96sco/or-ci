# Design

## Architecture

Add two generic modules beside the existing evidence-pack layer:

- `src/or_ci/formulation_adapter.py`
  - validates a small structured linear formulation shape;
  - converts it into OR-CI problem metadata;
  - emits a generic `build_model(data)` submission file that builds from the metadata instance;
  - keeps all external dataset labels as opaque metadata.
- `src/or_ci/evidence_batch.py`
  - reads a CSV manifest;
  - resolves row paths relative to the manifest location;
  - either uses existing `problem` + `submission` inputs or materializes them from `formulation`;
  - calls `verify` and `build_evidence_pack`;
  - writes per-record packs, generated inputs, a ledger CSV, and a summary JSON.

`src/or_ci/cli.py` gets a thin `evidence-batch` subcommand that delegates to `evidence_batch`.

## Manifest Contract

Required column:

- `record_id`

Existing OR-CI row:

- `statement`
- `problem`
- `submission`

Formulation row:

- `statement`
- `formulation`
- optional `problem_id`

The command rejects rows that have neither complete existing OR-CI inputs nor a formulation path. It continues past per-row formulation/verification failures and records them in the ledger.

## Linear Formulation Contract

The supported formulation shape is intentionally small and mirrors the existing external direct-LP audit:

- `vars`: list of variable names.
- `obj_declaration.direction`: minimize/maximize aliases.
- `obj_declaration.type`: `objective` with `terms`, or `objvar` with `vars`.
- `const_declarations`: list of supported linear constraints.

Supported constraint types:

- `linear`
- `lowerbound`
- `upperbound`
- `sum`
- `xby`
- `ratio`

Unsupported constraints raise an adapter error for that row. They do not change OR-CI verifier behavior.

## Materialized Problem Metadata

Generated problems use:

- `id`: supplied `problem_id` if present, otherwise `BWOR-BATCH-<n>`.
- `problem_type`: `LP`.
- `instance`: variable/objective/constraint data consumed by the generated submission.
- `metamorphic.cost_scaling`: scales `instance.objective.coefficients` by factor `2.0`.
- `evaluation_only`: only provenance fields and adapter non-claims; it must not reach `build_model`.

This produces verifier-only evidence. A candidate formulation that is source-unfaithful may still pass cost scaling, which is precisely the external OR-CI verifier-only evidence surface the paper needs.

## Output Layout

For `--out-dir <dir>`:

```text
<dir>/
  ledger.csv
  summary.json
  generated/
    <safe-record-id>/
      problem.json
      submission.py
  packs/
    <safe-record-id>.json
```

Existing-input rows do not duplicate their original problem/submission files; formulation rows write materialized files under `generated/`.

## Boundaries

- No natural-language parsing.
- No LLM/provider/network calls.
- No `or_llm_agent` imports.
- No source-fidelity claim from OR-CI `PASS`.
- No hardcoded external benchmark names in OR-CI code/tests.
- Dataset-specific research manifests live outside OR-CI.

## Compatibility

Existing `verify`, `validate-spec`, and `evidence-pack` commands are unchanged. The batch command reuses the existing report and evidence-pack schemas.

## Risks

- Generated submissions could hide adapter bugs. Mitigation: tests inspect generated problem/submission artifacts and run the real verifier path.
- Unsupported formulation features could reduce denominator coverage. Mitigation: row-level failure ledger preserves complete accounting.
- Users could overread verifier pass as source fidelity. Mitigation: summary and packs preserve explicit non-claims.
