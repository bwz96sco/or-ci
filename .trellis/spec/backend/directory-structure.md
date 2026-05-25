# Directory Structure

> Backend package layout and ownership rules for OR-CI.

---

## Overview

OR-CI is a small backend-only Python package installed from `src/or_ci`. It is
the standalone verifier for Operations Research Continuous Integration: it
loads JSON problem metadata, imports a submitted `build_model(data)` function,
extracts a Gurobi ModelIR, runs deterministic checks, and writes a JSON
verification report. It is not an LLM producer and must not contain OR-LLM-Agent
provider code.

This guide reflects the implemented layout in `src/or_ci/` and the archived
Phase 1 PRDs under `.trellis/tasks/archive/2026-05/`.

---

## Directory Layout

```text
or-ci/
├── pyproject.toml
├── src/
│   └── or_ci/
│       ├── __init__.py
│       ├── cli.py
│       ├── contracts.py
│       ├── metadata.py
│       ├── model_ir.py
│       ├── report.py
│       ├── scaling.py
│       ├── submission.py
│       └── verifier.py
└── tests/
    ├── conftest.py
    ├── fixtures/
    │   └── bwor/
    │       ├── BWOR-001/
    │       ├── BWOR-002/
    │       └── BWOR-010/
    └── or_ci/
        ├── test_cli.py
        ├── test_metadata.py
        ├── test_model_ir.py
        └── test_verifier.py
```

`pyproject.toml` defines the package as `or-ci`, the `or-ci` console script,
the `src` package layout, and the pinned Gurobi dependency. The relevant PRD
contract is archived at
`.trellis/tasks/archive/2026-05/05-15-or-ci-data-contracts-cli-report/prd.md`.

---

## Module Responsibilities

`src/or_ci/contracts.py` is the canonical vocabulary module. Put dataclasses,
Enums, and boundary-crossing shapes here: `Classification`,
`VerificationStatus`, `ProblemMetadata`, `ModelIR`, `CheckResult`, and
`VerificationReport`. Other modules should import these contracts rather than
redeclaring strings.

`src/or_ci/metadata.py` owns JSON metadata parsing and validation. It accepts
only structured JSON, validates `metamorphic.cost_scaling` and optional
`metamorphic.constraint_relaxation`, and retains `evaluation_only` only as
metadata. Do not import Gurobi or submission code from this module.

`src/or_ci/submission.py` owns untrusted submission import. It uses
`importlib.util.spec_from_file_location`, creates a unique module name from the
absolute path hash, and returns the callable `build_model`. Keep import
isolation here so verifier logic does not grow ad hoc module-loading code.

`src/or_ci/model_ir.py` owns Gurobi-to-ModelIR extraction. It calls
`model.update()`, rejects unsupported features, and reads variables,
linear/quadratic objective terms, and linear constraints through Gurobi
v12-compatible APIs. It must not optimize the model.

`src/or_ci/scaling.py` owns data transformations for metamorphic checks. It
deep-copies the `instance` subtree before scaling configured numeric paths. New
path-based transformations should reuse `scale_numeric_paths` or live beside it.

`src/or_ci/verifier.py` is the orchestration layer. It loads a problem, imports
a submission, calls `build_model(copy.deepcopy(problem.instance))`, extracts
ModelIR, optimizes original and transformed models, records `CheckResult`
objects, and maps outcomes to `Classification`.

`src/or_ci/report.py` serializes and reads JSON reports. Keep report file I/O
here; verifier code should return `VerificationReport`, not write files.

`src/or_ci/cli.py` owns `argparse` wiring for `verify` and `validate-spec`.
Keep it thin: path validation, command dispatch, and calls into metadata,
verifier, and report modules.

---

## Test Organization

Tests mirror the implemented module responsibilities:

- `tests/or_ci/test_metadata.py` covers metadata parsing and path scaling.
- `tests/or_ci/test_model_ir.py` covers ModelIR extraction and unsupported
  feature rejection using fake Gurobi-like models.
- `tests/or_ci/test_verifier.py` covers classification behavior and BWOR
  fixture outcomes.
- `tests/or_ci/test_cli.py` covers `validate-spec`, `verify`, and report shape.

Fixtures live under `tests/fixtures/bwor/<BWOR-ID>/` with:

- `problem.json`
- `correct.py`
- `runtime_error.py`
- `wrong.py`
- `wrong_constraint.py`

The fixture task contract is archived at
`.trellis/tasks/archive/2026-05/05-15-or-ci-bwor-micro-pilot-fixtures/prd.md`.

---

## Naming Conventions

- Python modules use lower-case snake_case.
- Public classification values use exact uppercase Enum spellings from
  `Classification`: `SUCCESS`, `SYNTAX_OR_RUNTIME_ERROR`,
  `SOLVER_STATUS_ERROR`, `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL`, and
  `UNSUPPORTED_MODEL_FEATURE`.
- Problem IDs use `BWOR-NNN`; do not introduce NL4OR identifiers in new OR-CI
  code, tests, fixtures, paths, or comments.
- Metamorphic check names are lower-case keys matching metadata and report
  checks: `original_solver_status`, `cost_scaling`, and
  `constraint_relaxation`.
- Submission fixtures must expose `def build_model(data: dict) -> gurobipy.Model`
  when they are normal Gurobi submissions.

---

## Adding New Verifier Behavior

Add new cross-module data fields to `contracts.py` first. Add JSON validation to
`metadata.py`, reusable instance transformations to `scaling.py`, and verifier
orchestration to `verifier.py`. Add fixture coverage under `tests/fixtures/bwor`
or a new benchmark-specific fixture root only when the benchmark naming and
metadata contract are explicit.

New solver-inspection support belongs in `model_ir.py` only if it remains within
the supported Gurobi model surface. The current supported extension surface is
linear LP/MILP plus QP/MIQP quadratic objectives. NLP, quadratic constraints,
Gurobi multi-objective models, and general constraints are out of scope unless a
new PRD explicitly changes that boundary.

---

## Anti-Patterns

- Do not put Gurobi imports in `metadata.py`; metadata loading must stay JSON-only.
- Do not add OpenAI, Anthropic, dotenv, prompt, or Codex provider code to OR-CI.
  Producer logic belongs in `or_llm_agent`.
- Do not pass the full metadata object to `build_model`; pass only the instance
  subtree.
- Do not let `model_ir.py` optimize models. Optimization belongs in
  `verifier.py`.
- Do not duplicate classification strings in tests or modules when importing
  `Classification` is possible.
- Do not cross-import between `verifier.py` and `model_ir.py` in both directions;
  `verifier.py` may depend on extractors, but extractors must remain standalone.
