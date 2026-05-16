# Fill OR-CI backend ops spec (error handling + logging)

## Goal

Fill `.trellis/spec/backend/error-handling.md` and `.trellis/spec/backend/logging-guidelines.md` so they document how the OR-CI verifier classifies failures, isolates the submission under test, and reports results.

These two files describe the **operational** discipline of the verifier — how it survives broken submissions and produces useful output.

## Project Context

OR-CI Phase 1 is a Python CLI verifier that imports an arbitrary user-supplied Gurobi submission and runs metamorphic checks on it. Phase 1a ships cost-scaling; the 2026-05-16 continuation adds a configured constraint-relaxation check (schema TBD, no implementation PRD yet). Because submissions can be syntactically broken, raise at runtime, or build wrong models, the verifier MUST treat each submission as untrusted input and classify every failure deterministically — the same classification taxonomy MUST cover both checks.

The output of every run is a JSON report (no log files, no DB). The CLI is `uv run or-ci verify --problem <p.json> --submission <m.py> --out <r.json>`.

**Canonical vocabulary lives in `.trellis/spec/backend/data-contracts.md`.** Quote those classification enum values, status names, and report field names verbatim — do not invent new ones.

## Required Reading (do this first)

1. `.trellis/spec/backend/data-contracts.md` — the **single source of truth** for classification values and report fields. Read it first.
2. `.trellis/spec/backend/index.md` — project scope.
3. `.trellis/tasks/05-15-or-ci-cost-scaling-verifier/prd.md` — exact failure classification list, invariant, classification rules.
4. `.trellis/tasks/05-15-or-ci-gurobi-modelir-extractor/prd.md` — `UNSUPPORTED_MODEL_FEATURE` path and how extractor failures bubble up.
5. `.trellis/tasks/05-15-or-ci-data-contracts-cli-report/prd.md` — report schema, "passing means no tested invariant failed" rule.
6. `.trellis/tasks/05-15-or-ci-bwor-micro-pilot-fixtures/prd.md` — what kinds of fixtures exist (correct / syntax-error / runnable-but-wrong) so you know what each classification has to cover.

## Tools Available

You are running as a Codex agent. The following MCP servers are configured for this project:

### GitNexus MCP (available but limited usefulness here)
| Tool | Purpose |
|------|---------|
| `gitnexus_query` | Find execution flows by concept |
| `gitnexus_context` | 360-degree symbol view |

There is no OR-CI source code yet. The PRDs are the real source.

### Filesystem (primary)
Use Read/Grep on `.trellis/spec/backend/data-contracts.md` and the task PRDs.

## Files to Fill

### 1. `.trellis/spec/backend/error-handling.md`

Sections to write:

- **Overview** — One paragraph: the verifier treats submissions as untrusted, never crashes the CLI, and always emits a classified JSON report.
- **Failure Classification Taxonomy** — Table mapping each classification value (taken from `data-contracts.md`) to:
  - When it is emitted (which check, which exception type).
  - What the `failures` and `possible_causes` entries should contain.
  - Whether it is a verifier bug or a submission/problem issue.
- **Isolation Rules** — How to safely import a user submission (`importlib.util.spec_from_file_location`-style; document the pattern). What exceptions get caught at the import boundary vs. at `build_model` invocation vs. at `model.optimize()`.
- **Deep-Copy Discipline** — Verifier MUST deep-copy the metadata `instance` subtree before applying cost-scaling transformations. Document why (avoid mutating original; avoid leaking transformed data into subsequent checks).
- **`evaluation_only` Discipline** — The verifier MUST retain `evaluation_only` in loaded metadata but NEVER pass it into `build_model`. This is a critical anti-leak rule, not a stylistic preference. Document the exact code pattern (pass `metadata["instance"]`, not `metadata`).
- **Solver Status Handling** — When optimal status is required (cost-scaling pre/post), non-optimal status maps to `SOLVER_STATUS_ERROR`. Document expected Gurobi status codes and how they map.
- **Anti-Patterns** — Examples:
  - Catching `Exception` and swallowing it without classification.
  - Passing the full metadata dict to `build_model`.
  - Mutating `metadata["instance"]` in place during cost scaling.
  - Calling `model.optimize()` inside the extractor.
  - Asserting variable-value equality between original and scaled runs.

### 2. `.trellis/spec/backend/logging-guidelines.md`

OR-CI is unusual: the **JSON report IS the primary output**, not stdout text logs. Sections:

- **Output Channels** —
  - `--out <path.json>`: the canonical report (every classification, every check, every cause).
  - `stdout`: a short human-readable summary line (one line per run).
  - `stderr`: developer diagnostics (Gurobi version, traceback for unexpected verifier bugs only — submission errors go in the report, NOT stderr).
- **Report-First Discipline** — All submission outcomes (success / runtime error / wrong answer) MUST be in the JSON report. Stderr is reserved for verifier-internal problems (e.g., bad CLI args, fatal config).
- **Information Leak Rules** — The verifier MUST NOT:
  - Print `evaluation_only.answer` or `evaluation_only.label` to stdout, stderr, or the report (the report has no field for them).
  - Print the full submission source code on error.
  - Make network calls or invoke LLM APIs.
- **Gurobi Output** — Gurobi's solver log should be suppressed by default (`Model.Params.OutputFlag = 0`) so CLI runs are quiet; surface only via the report's `solver_status` and `model_ir_summary`.
- **Determinism** — Tests must run with `OutputFlag = 0` and avoid wall-clock-dependent fields in the report.
- **Anti-Patterns** —
  - Writing a separate log file alongside the report.
  - Using `print()` for submission errors instead of the report's `failures` array.
  - Leaving Gurobi's default verbose output enabled.
  - Logging `evaluation_only` values anywhere.

## Important Rules

### Stay in your lane
- ONLY modify `.trellis/spec/backend/error-handling.md` and `.trellis/spec/backend/logging-guidelines.md`.
- DO NOT modify other spec files, task files, source files, or run git commands.
- You may read any file for analysis.

### Quote, don't invent
- All classification enum values, report field names, and JSON keys MUST come from `.trellis/spec/backend/data-contracts.md` or the implementation PRDs. Quote, don't paraphrase.
- If `data-contracts.md` is still a placeholder when you read it (the orchestrator runs all spec tasks in parallel), fall back to the PRDs in `.trellis/tasks/05-15-or-ci-*/`.

### No invented features
v1 is Gurobi linear only. Don't document NLP/QP/multi-obj handling. Constraint-relaxation IS in-scope (2026-05-16 continuation) — but its detailed contract has no PRD; cover it only at the invariant level ("optimal objective weakly improves after relaxation") and ensure the classification taxonomy / isolation rules / deep-copy discipline apply to it just as to cost-scaling.

## Acceptance Criteria

- [ ] Both files have no remaining `(To be filled ...)` placeholders.
- [ ] Classification taxonomy table covers every value from data-contracts.md.
- [ ] `evaluation_only` anti-leak rule appears in BOTH files (error-handling under discipline; logging under info-leak rules).
- [ ] At least 3 anti-patterns documented in each file.
- [ ] Gurobi `OutputFlag = 0` rule appears in logging guidelines.
- [ ] Each file cites at least 2 PRD paths or the data-contracts.md path.

## Technical Notes

- Repo path: `/Users/zhangbowen/Projects/OR/code/or-ci`
- Language: English.
- Do NOT modify `data-contracts.md` or `directory-structure.md`; if you find a gap there, note it as a comment in your own spec files, do not edit theirs.
