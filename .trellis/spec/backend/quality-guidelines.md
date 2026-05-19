# Quality Guidelines

> Code quality standards for OR-CI backend development.

---

## Overview

OR-CI quality means predictable classification, reproducible reports, and a
small dependency surface. The package is a deterministic verifier, not a solver
research sandbox and not an LLM generation system. Every change should preserve
the boundary described in `.trellis/spec/backend/data-contracts.md`.

---

## Toolchain

Use `uv` for Python commands:

```bash
uv run or-ci verify --problem <p.json> --submission <m.py> --out <r.json>
uv run or-ci validate-spec --problem <p.json>
uv run pytest
```

Project requirements:

- Python `>=3.10`.
- `gurobipy==12.0.1`.
- stdlib `json` for metadata and report I/O.
- `pytest` for tests.
- `argparse` for CLI wiring.

Do not document raw `python`, raw `pytest`, or ad hoc environment commands as
the normal workflow.

---

## Required Patterns

- Type annotate public functions and dataclasses.
- Put shared data shapes and enums in `src/or_ci/contracts.py`.
- Use `pathlib.Path` for filesystem paths.
- Use stdlib `json` for metadata and report files.
- Keep CLI logic thin in `src/or_ci/cli.py`; delegate to metadata, verifier, and
  report modules.
- Pass only `copy.deepcopy(problem.instance)` into the original `build_model`
  call.
- Use `scale_numeric_paths` / `scaled_instance` for path-based metamorphic
  transformations so deep-copy behavior stays centralized.
- Call `model.update()` before reading Gurobi variables, constraints, objective,
  or model attributes in ModelIR extraction.
- Suppress solver output with `OutputFlag = 0`.
- Serialize reports with stable JSON formatting.

---

## Forbidden Patterns

- PyYAML or any YAML library: Phase 1 metadata is JSON only.
- NL4OR names in new OR-CI code, tests, fixtures, paths, or comments: use BWOR
  naming only.
- LLM API calls, network calls, model-provider code, prompt code, or dotenv
  loading: OR-CI is the verifier, not the producer.
- `print()` for submission failure reporting: use the JSON report's `failures`
  array.
- Catching `Exception` without mapping to the verifier taxonomy.
- Passing the full metadata dict into `build_model`: it leaks
  `evaluation_only`.
- Calling `model.optimize()` inside `model_ir.py`.
- Asserting identical variable values between original and scaled runs.
- Mutating shared metadata in place during cost scaling or constraint relaxation.
- Reaching into `../or_llm_agent` evaluation scripts from OR-CI verifier code.
- Adding QP, NLP, multi-objective, SOS, general constraint, or full proof
  support without a new explicit PRD and test plan.

---

## Testing Requirements

`uv run pytest` is the full test gate. Required coverage:

- Metadata loader rejects missing required fields.
- `validate-spec` accepts valid metadata and reports metadata validation errors.
- Verifier never passes `evaluation_only` into `build_model`.
- ModelIR extraction preserves variables, objective sense, objective
  coefficients, constraints, and summary counts.
- Unsupported ModelIR features raise `UnsupportedModelFeature`.
- Correct BWOR fixtures classify as `SUCCESS`.
- Runtime-error fixtures classify as `SYNTAX_OR_RUNTIME_ERROR`.
- Wrong cost fixtures classify as `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL` with
  `check == "cost_scaling"`.
- Wrong constraint fixtures pass cost scaling but fail
  `constraint_relaxation`.
- CLI smoke writes a valid report file with all canonical top-level keys.

Tests must be deterministic under the pinned Gurobi version, use `OutputFlag = 0`,
and avoid network calls and LLM APIs. This mirrors
`.trellis/tasks/archive/2026-05/05-15-or-ci-pytest-cli-acceptance/prd.md`.

---

## Coverage-Miss Discipline

Passing OR-CI means no configured invariant failed. It is not a proof that a
model is fully correct. If a known-wrong fixture passes cost scaling, treat it as
a coverage miss unless the configured invariant itself was implemented
incorrectly. Add another targeted metamorphic check or fixture rather than
overclaiming correctness.

The cost-scaling PRD explicitly allows wrong fixtures that cost scaling cannot
detect to be reported as coverage misses:
`.trellis/tasks/archive/2026-05/05-15-or-ci-cost-scaling-verifier/prd.md`.

---

## Code Review Checklist

- Problem IDs and fixture paths use BWOR naming only.
- No PyYAML, network, dotenv, OpenAI, Anthropic, or LLM dependency was added.
- `evaluation_only` is retained only in metadata and never reaches
  `build_model`.
- Transformations deep-copy instance data before mutation.
- ModelIR extraction calls `model.update()` and does not optimize.
- New failures map to a canonical `Classification`.
- Reports keep the canonical top-level JSON fields.
- Tests cover success, runtime failure, semantic failure, and CLI report output.
- Solver output is quiet by default.
- New verifier logic does not import from `or_llm_agent`.

---

## Out-of-Scope Reminders

The archived parent PRD excludes the LLM generation pipeline, Trellis check
integration, symmetry permutation, NLP/QP/multi-objective support, and full
30-50 problem experiments:
`.trellis/tasks/archive/2026-05/05-15-or-ci-phase-1-micro-pilot/prd.md`.

Constraint relaxation was described as a later continuation in the spec PRDs and
is now implemented for selected linear fixtures. Do not treat that as permission
to add broad constraint-equivalence proving or unsupported Gurobi feature
support.
