# PRD: OR-CI Integration Pilot

Date: 2026-05-16

## Objective

Run a first integration pilot where `or_llm_agent` acts as the producer of Gurobi model submissions and standalone OR-CI acts as the verifier.

## Scope

- Use the three existing OR-CI BWOR fixtures:
  - `BWOR-001`
  - `BWOR-002`
  - `BWOR-010`
- Use `or_llm_agent` only as a producer. Do not move OR-CI verifier logic into `or_llm_agent`.
- Generate Python submissions that expose:

```python
def build_model(data: dict) -> gurobipy.Model:
    ...
```

- Verify each generated submission with:

```bash
uv run or-ci verify --problem ... --submission ... --out ...
```

## Outputs

- Generated submission files.
- Raw LLM responses.
- OR-CI JSON verification reports.
- A Markdown pilot report with aggregate classification counts and per-problem outcomes.

## Acceptance Criteria

- The pilot can be rerun with one command from the `or_llm_agent` uv environment.
- The pilot writes deterministic artifacts under `artifacts/pilot/phase-1-integration-2026-05-16/`.
- The report distinguishes generation failures from OR-CI verification classifications.
- OR-CI remains standalone and does not gain OpenAI, Anthropic, or dotenv runtime dependencies.

## Non-Goals

- Do not scale beyond the three Phase 1 BWOR fixtures yet.
- Do not modify OR-CI verifier semantics during this pilot unless a verifier bug is found.
- Do not treat `SUCCESS` as proof of full model correctness.
- Do not perform paper-scale 30-50 problem evaluation in this task.
