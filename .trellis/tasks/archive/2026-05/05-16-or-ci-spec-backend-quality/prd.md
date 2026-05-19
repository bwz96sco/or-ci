# Fill OR-CI backend quality spec (uv + pytest + forbidden patterns)

## Goal

Fill `.trellis/spec/backend/quality-guidelines.md` so it documents the OR-CI Phase 1 quality bar: build/test workflow (uv + pytest), forbidden patterns (NL4OR naming, PyYAML, LLM calls in v1), required patterns (type hints, deterministic tests), and the review checklist.

## Project Context

OR-CI Phase 1 is a Python CLI verifier built with:

- **Python ≥ 3.10**
- **uv** for environment management (`uv run or-ci verify ...`, `uv run pytest`)
- **gurobipy 12.0.1** as the only solver
- **stdlib `json`** for metadata (no PyYAML)
- **pytest** as the test framework
- **No LLM calls, no network calls** in v1
- **BWOR naming only** (no NL4OR names in code, tests, fixtures, or docs)

The implementation will be added to the sibling repo `../or_llm_agent` (per most PRDs) — keep that in mind when describing tooling.

## Required Reading (do this first)

1. `.trellis/spec/backend/index.md` — project scope, declared file set.
2. `.trellis/spec/backend/data-contracts.md` — canonical names; quote them when forbidding alternatives.
3. `.trellis/tasks/05-15-or-ci-phase-1-micro-pilot/prd.md` — scope, "use BWOR naming only", "use JSON metadata not YAML", out-of-scope list.
4. `.trellis/tasks/05-15-or-ci-data-contracts-cli-report/prd.md` — pytest as dev dep, no PyYAML.
5. `.trellis/tasks/05-15-or-ci-pytest-cli-acceptance/prd.md` — required test coverage list, "tests avoid network calls and do not invoke LLM APIs", determinism rule.
6. `.trellis/tasks/05-15-or-ci-cost-scaling-verifier/prd.md` — "do not assert identical variable values" — a test-discipline rule.

## Tools Available

You are running as a Codex agent. MCP servers configured for this project:

### GitNexus MCP (available but limited)
There is no OR-CI source code yet. PRDs are the source of truth.

### Filesystem (primary)
Use Read/Grep on the PRDs and the other backend spec files.

## File to Fill

### `.trellis/spec/backend/quality-guidelines.md`

Sections to write:

- **Overview** — One paragraph: OR-CI is small, deterministic, and dependency-light. Quality = predictable classification on every run + reproducible test runs.
- **Toolchain** — Required commands:
  - `uv run or-ci verify --problem <p.json> --submission <m.py> --out <r.json>` (CLI smoke).
  - `uv run pytest` (full test run).
  - Python ≥ 3.10, gurobipy 12.0.1 pinned, pytest as dev dep.
  - All Python invocations through uv — do not document raw `python` or `pytest` calls.
- **Required Patterns**:
  - Type hints on every public function (mypy-friendly even if mypy isn't run yet).
  - Stdlib `json` for metadata I/O. `pathlib.Path` for paths.
  - `argparse` for the CLI; subcommand `verify` with `--problem`, `--submission`, `--out` flags.
  - `copy.deepcopy` before any metamorphic transformation (cross-link to error-handling.md's deep-copy rule).
  - `model.update()` before reading Gurobi attributes (cross-link to data-contracts.md ModelIR section).
  - Deterministic tests: `OutputFlag = 0`, no wall-clock fields, no random seeds beyond what fixtures fix.
- **Forbidden Patterns** (with the one-line "why"):
  - PyYAML or any YAML lib — JSON only (per Phase 1 PRD).
  - NL4OR names anywhere in new code, tests, fixtures, paths, or comments — BWOR only.
  - LLM API calls, network calls, file downloads — Phase 1 has no LLM integration.
  - `print()` for failure reporting — failures go in the JSON report (cross-link to logging-guidelines.md).
  - Catching `Exception` without classifying into the verifier's taxonomy.
  - Passing the full metadata dict (including `evaluation_only`) into `build_model`.
  - Calling `model.optimize()` inside the ModelIR extractor.
  - Asserting identical variable values between original and scaled runs (the cost-scaling invariant is on the objective only).
  - Mutating shared metadata in place during a metamorphic transformation.
  - Reaching out to `../or_llm_agent`'s existing eval scripts or any LLM glue.
- **Testing Requirements** (mirror the pytest-cli-acceptance PRD):
  - Metadata loader rejects missing required fields.
  - Verifier never passes `evaluation_only` into `build_model` (test by injecting a sentinel).
  - ModelIR extraction returns expected variables, constraints, objective sense, summary counts.
  - Correct fixtures → `SUCCESS`.
  - Syntax/runtime fixtures → `SYNTAX_OR_RUNTIME_ERROR`.
  - At least one wrong fixture → `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL`.
  - CLI smoke writes a valid report file.
  - Tests must be deterministic under the pinned Gurobi version.
  - Tests must avoid network and LLM calls.
- **Coverage-Miss Discipline** — When a wrong fixture passes cost-scaling, report it as a coverage miss in test assertions, NOT as a framework bug (per cost-scaling-verifier PRD).
- **Code Review Checklist** — Short bullet list reviewers must verify on every OR-CI PR: BWOR-only naming check, no PyYAML/LLM/network, deep-copy used, `model.update()` called, classification covers every exception, `evaluation_only` never reaches `build_model`, deterministic tests.
- **Out-of-Scope Reminders** — Explicitly call out v1 exclusions per the parent PRD: LLM generation pipeline, Trellis check integration, symmetry permutation, NLP/QP/multi-obj, full 30–50 problem experiments. **Note:** the parent PRD lists constraint relaxation as out-of-scope, but the 2026-05-16 continuation added it as an emerging in-scope check (no implementation PRD yet). Document this conflict briefly and treat constraint-relaxation as in-scope-but-stubbed; do not enforce v1 forbidden patterns against it (only against the listed exclusions).

## Important Rules

### Stay in your lane
- ONLY modify `.trellis/spec/backend/quality-guidelines.md`.
- DO NOT modify other spec files, task files, source files, or run git commands.
- You may read any file for analysis.

### Cross-link, don't duplicate
- For data-shape rules (ModelIR fields, classification values), link to `data-contracts.md` rather than restating.
- For deep-copy / `evaluation_only` / Gurobi `OutputFlag` rules, link to `error-handling.md` / `logging-guidelines.md`.

### No invented features
- Do not document linters (ruff, black, mypy) as required unless they appear in a PRD. The PRDs do NOT mandate them — list them as "may be added" at most.

## Acceptance Criteria

- [ ] No remaining `(To be filled ...)` placeholder text.
- [ ] Toolchain section lists exact `uv` commands from the PRDs.
- [ ] Forbidden patterns list contains at minimum: PyYAML, NL4OR names, LLM/network calls, `print()` for failures, blanket `Exception` swallow, full-metadata-into-build_model, optimize-in-extractor, asserting variable-value equality.
- [ ] Required patterns include deep-copy, `model.update()`, type hints, deterministic tests.
- [ ] Code review checklist has at least 6 items.
- [ ] Out-of-Scope Reminders section explicitly mirrors the parent PRD's exclusions.
- [ ] Cites at least 3 implementation PRD paths.

## Technical Notes

- Repo path: `/Users/zhangbowen/Projects/OR/code/or-ci`
- Implementation repo per most PRDs: `../or_llm_agent`. The pytest-cli-acceptance PRD says "this standalone OR-CI repo" — note the discrepancy briefly under Toolchain but do not try to resolve it.
- Language: English.
