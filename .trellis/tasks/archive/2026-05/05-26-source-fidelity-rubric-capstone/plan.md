# Structured Source-Fidelity Rubric Plan

## Summary And Goal

Build a structured source-fidelity rubric in OR-LLM-Agent so the report can distinguish:

- OR-CI verification pass: generated `ProblemSpec` and generated code are internally consistent.
- Source-fidelity pass: generated `ProblemSpec` faithfully preserves the original source statement, data, units, objective, constraints, and supported scope.
- Provisional/unsupported cases: cases that pass inner verification but should not support a paper claim.

The goal is not to prove mathematical correctness. The goal is to create an auditable review layer that prevents material false accepts and produces a capstone report with clear claim boundaries.

Implement this in OR-LLM-Agent only. OR-CI remains the deterministic inner verifier.

## Key Changes

Update `src/or_llm_agent/cli.py` so fidelity review output includes a versioned rubric:

```json
{
  "rubric_version": "source_fidelity_v1",
  "status": "accepted | rejected",
  "confidence": 0.0,
  "dimensions": {
    "source_suitability": {},
    "data_completeness": {},
    "sets_and_indices": {},
    "numeric_parameters": {},
    "action_space": {},
    "objective": {},
    "units_and_scaling": {},
    "constraint_families": {},
    "metamorphic_coverage": {},
    "clarification_dependency": {},
    "materiality": {}
  },
  "issues": [],
  "review_note": "",
  "evidence": []
}
```

Each dimension must contain:

```json
{
  "status": "pass | warn | fail | not_applicable",
  "severity": "none | minor | major | critical",
  "finding": "one sentence",
  "evidence": ["source-backed observation"],
  "artifact_refs": ["statement", "spec/problem.json", "reports/..."]
}
```

Acceptance rules:

- Reject if any required hard-block dimension has `status="fail"` with `severity="major"` or `severity="critical"`.
- Hard-block dimensions are `data_completeness`, `action_space`, `objective`, `units_and_scaling`, and `constraint_families`.
- Accept only when key dimensions are reviewed and no unresolved major/critical source-fidelity issue remains.
- Treat agent-generated clarification assumptions as provisional, not as human clarification.
- If provisional assumptions affect objective, action space, units, or required data, mark `clarification_dependency` as at least `warn/major`.
- Preserve existing statuses for compatibility: `accepted`, `rejected`, `llm_accepted`, `llm_rejected`, `not_reviewed`.

Extend the review prompt created by `_build_fidelity_review_agent_prompt(...)` so the nested reviewer must return the rubric schema and explicitly separate:

- facts present in the source statement,
- facts derived from generated artifacts,
- human/source clarification,
- provisional agent assumptions.

Extend `apply_fidelity_review(...)` and fidelity markdown/json writers so every reviewed case records:

- `spec_fidelity_rubric_version`
- `spec_fidelity_failed_dimensions`
- `spec_fidelity_blocking_dimension_count`
- `spec_fidelity_warning_dimension_count`
- `spec_fidelity_provisional`
- `spec_fidelity_materiality`

Add preflight risk flags to the initial fidelity payload for known weak spots:

- missing or incomplete numeric data,
- unsupported stochastic policy or unsupported source scope,
- provisional clarification dependency,
- multi-scenario objective undercheck,
- routing/TSP cost-scaling-only validation,
- MIQP or pairwise-cost unit/scaling sensitivity,
- missing constraint-relaxation evidence.

These flags inform review; they do not replace the rubric decision.

## Verification Plan

Add focused tests in `tests/test_problemspec_generation.py`:

- Agent review with complete rubric stores dimension results and updates summary fields.
- Agent review missing rubric dimensions is rejected as rubric-incomplete.
- A review that says `accepted` is still rejected if a hard-block dimension fails.
- Failed OR-CI verification still cannot be accepted by fidelity review.
- Provisional clarification creates `spec_fidelity_provisional=true` and a clarification warning.
- Multi-scenario objective undercheck creates a risk flag.
- Routing/TSP cost-scaling-only validation creates a risk flag.
- Batch review writes aggregate dimension counts and capstone report artifacts.
- Legacy/manual flat review remains readable but is marked `legacy-flat` and excluded from rubric-complete aggregate metrics.

Run:

```bash
uv run pytest tests/test_problemspec_generation.py
uv run pytest tests
```

For capstone validation, run the rubric on copied or fixture-based cases representing:

- BWOR-020-style incomplete dataset: must fail `data_completeness`.
- BWOR-061-style unsupported stochastic boundary: must fail or warn on `source_suitability`.
- BWOR-027-style routing/TSP cost-scaling weakness: must flag `metamorphic_coverage` or `units_and_scaling`.
- BWOR-051-style multi-scenario objective weakness: must flag `objective`.
- BWOR-082-style MIQP/pairwise unit ambiguity: must flag `units_and_scaling`.
- Clarification-dependent cases: must be marked provisional unless backed by human/source clarification.

Do not require live nested Codex/Oracle calls for automated verification; use patched reviewer payloads and fixtures for deterministic tests.

## Capstone Report Output

Add a batch-level capstone artifact written after fidelity batch review:

- `fidelity-rubric-summary.json`
- `fidelity-rubric-report.md`

The markdown report must include:

- Clear goal statement: source-fidelity review of generated `ProblemSpec` against source problem statements.
- Claim boundary: generated-code PASS is not equivalent to source-fidelity PASS.
- Aggregate counts:
  - total cases,
  - OR-CI verified cases,
  - rubric-reviewed cases,
  - accepted/rejected/not-reviewed cases,
  - provisional cases,
  - major/critical failures by dimension.
- Case matrix with:
  - problem id,
  - OR-CI verification status,
  - fidelity status,
  - failed/warned dimensions,
  - provisional flag,
  - materiality,
  - artifact path.
- Boundary taxonomy:
  - source/data invalid,
  - unsupported modeling scope,
  - source mismatch,
  - verifier weakness,
  - provisional clarification.
- Capstone conclusion:
  - strongest defensible claim,
  - weakest evidence category,
  - cases excluded from headline claims,
  - recommended next experiment/report action.

The capstone should support a report sentence like:

> Among OR-CI-verified generated models, source-fidelity review accepted N cases, rejected M cases, and marked K as provisional; therefore the defensible claim is about layered acceptance and false-accept exposure, not raw solve count.

## Assumptions

- First implementation touches OR-LLM-Agent only, mainly `src/or_llm_agent/cli.py` and fidelity tests.
- Existing OR-CI behavior and schemas remain unchanged.
- The rubric is a review artifact, not a new mathematical verifier.
- Human/source clarification is stronger evidence than agent assumptions.
- Agent assumptions must remain visible in the capstone and cannot silently upgrade a case into a source-faithful success.
