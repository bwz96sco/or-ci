# Source Fidelity Rubric Design

## Boundaries

- OR-CI remains a deterministic verifier and receives no LLM, provider, prompt, or source-fidelity review code.
- OR-LLM-Agent owns the source-fidelity rubric, case review persistence, and batch capstone output.
- The existing fidelity commands remain the public surface: `review-fidelity`, `review-fidelity-batch`, `resolve-fidelity`, and `resolve-fidelity-batch`.

## Rubric Contract

Rubric-complete reviews use `rubric_version="source_fidelity_v1"` and include the required dimension keys:

- `source_suitability`
- `data_completeness`
- `sets_and_indices`
- `numeric_parameters`
- `action_space`
- `objective`
- `units_and_scaling`
- `constraint_families`
- `metamorphic_coverage`
- `clarification_dependency`
- `materiality`

Each dimension stores `status`, `severity`, `finding`, `evidence`, and `artifact_refs`.

Legacy flat reviews remain supported. They are stored with `rubric_version="legacy-flat"` and are not counted as rubric-complete in capstone metrics.

## Decision Rules

- Agent-mode review results must include all required dimensions, or the review is coerced to `llm_rejected` with a rubric-incomplete note.
- Manual flat reviews can remain accepted or rejected for backward compatibility.
- A review cannot accept a case whose OR-CI verification did not pass.
- A review that claims acceptance is coerced to rejected when a hard-block dimension has `status="fail"` and `severity` in `major` or `critical`.
- Hard-block dimensions are `data_completeness`, `action_space`, `objective`, `units_and_scaling`, and `constraint_families`.
- Provisional clarification dependencies do not automatically reject a case, but they set `spec_fidelity_provisional=true` and must appear in case and capstone reports.

## Persistence And Reporting

Per case, `spec/fidelity-review.json` stores the normalized review, rubric version, dimensions, automatic checks, and risk flags. `summary.json` receives compact fields for batch aggregation.

Per case, `spec/fidelity-review.md` shows existing review metadata plus a rubric table when dimensions exist.

Per batch, review output writes:

- `fidelity-rubric-summary.json` for machine-readable aggregate metrics.
- `fidelity-rubric-report.md` for report/capstone reading.
- The existing `report.md` includes links to these capstone artifacts when present.

## Risk Flags

Initial unreviewed fidelity payloads receive warning flags for source-fidelity risks that can be inferred from existing summary/spec/report artifacts. These flags guide reviewers and capstone taxonomy; they do not by themselves prove a mismatch.

## Compatibility

- Existing flat review JSON remains readable.
- Existing command names and default modes remain unchanged.
- Existing summary fields remain populated.
- New summary fields are additive.
