# Backend Development Guidelines

> Conventions for the OR-CI verifier — a Python CLI that loads structured problem metadata, imports a handwritten Gurobi submission, extracts a linear ModelIR, runs metamorphic checks, and writes a JSON report.

---

## Overview

OR-CI Phase 1 is a backend-only Python package (`or_ci`) installed via uv. It exposes a `uv run or-ci verify ...` entrypoint and has no frontend, no database, and no network calls.

These guidelines describe how to write and review code for that package.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | `or_ci` package layout, module boundaries, file roles | Filled |
| [Data Contracts](./data-contracts.md) | Problem metadata JSON, `build_model` submission contract, ModelIR, report JSON | Filled |
| [Error Handling](./error-handling.md) | Failure classification taxonomy, isolation rules, deep-copy discipline | Filled |
| [Logging Guidelines](./logging-guidelines.md) | JSON report as primary output, stderr for diagnostics, no LLM/network info leak | Filled |
| [Quality Guidelines](./quality-guidelines.md) | uv + pytest workflow, BWOR-only naming, no-LLM-in-v1 rule, forbidden patterns | Filled |

---

## Scope Notes

- **No frontend.** OR-CI Phase 1 is a CLI verifier. Any user-facing surface is the CLI flags and the JSON report.
- **No database.** All state is in JSON files and in-memory Python objects.
- **v1 = Gurobi linear only.** Phase 1a covers cost scaling; the 2026-05-16 continuation adds configured constraint-relaxation checks over numeric instance paths. QP, NLP, multi-objective, and full constraint-equivalence solving are out of scope.
- **BWOR naming only.** Do not introduce NL4OR names in new code, tests, fixtures, or docs.

---

## How to Fill These Guidelines

For each guideline file:

1. Document the project's **actual conventions** as defined by the Phase 1 PRDs (`.trellis/tasks/05-15-or-ci-*/prd.md`).
2. Include **code examples** that match the Phase 1 contracts (Gurobi 12 calls, `build_model` signature, JSON metadata shape).
3. List **forbidden patterns** and why (e.g., passing `evaluation_only` into `build_model`).
4. Cross-reference **canonical vocabulary** defined in `data-contracts.md` rather than redefining names.

---

**Language**: All documentation should be written in **English**.
