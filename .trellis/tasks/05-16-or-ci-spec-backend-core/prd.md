# Fill OR-CI backend core spec (directory structure + data contracts)

## Goal

Fill `.trellis/spec/backend/directory-structure.md` and `.trellis/spec/backend/data-contracts.md` so they document the **Phase 1 OR-CI verifier** package layout and all data shapes that cross module boundaries.

These two files define the foundational vocabulary that the **ops** and **quality** spec tasks reference. Be precise — other tasks will quote your canonical names verbatim.

## Project Context

OR-CI Phase 1 is a Python CLI verifier that:

1. Loads structured problem metadata from JSON.
2. Imports a handwritten Gurobi submission exposing `build_model(data) -> gurobipy.Model`.
3. Extracts a linear ModelIR from the built Gurobi model.
4. Runs metamorphic checks against the model.
5. Classifies failures and writes a JSON report.

### Scope (two waves)

- **Phase 1a (fully PRD'd)** — cost-scaling metamorphic check. See `.trellis/tasks/05-15-or-ci-cost-scaling-verifier/prd.md`.
- **2026-05-16 continuation (no implementation PRD yet)** — configured **constraint-relaxation** checks over numeric instance paths. The verifier framework must accommodate it but the spec should mark the contract as **emerging / stubbed** rather than invent details.

The implementation will live in a Python package named `or_ci`, installed via uv. The CLI entrypoint is `uv run or-ci verify --problem <p.json> --submission <m.py> --out <r.json>`.

Tech stack: Python ≥3.10, gurobipy 12.0.1, stdlib `json` (no PyYAML), pytest for tests.

**There is no existing source code yet** — these specs describe the design that the implementation PRDs (`.trellis/tasks/05-15-or-ci-*/prd.md`) will be built to.

## Required Reading (do this first)

Read ALL of these before drafting — they are the source of truth:

1. `.trellis/tasks/05-15-or-ci-phase-1-micro-pilot/prd.md` — parent task, scope, acceptance criteria.
2. `.trellis/tasks/05-15-or-ci-data-contracts-cli-report/prd.md` — public contracts, CLI shape, metadata example, report fields.
3. `.trellis/tasks/05-15-or-ci-gurobi-modelir-extractor/prd.md` — ModelIR field list and Gurobi API used.
4. `.trellis/tasks/05-15-or-ci-cost-scaling-verifier/prd.md` — cost-scaling invariant and classification names.
5. `.trellis/tasks/05-15-or-ci-bwor-micro-pilot-fixtures/prd.md` — fixture layout and metadata rules.
6. `.trellis/tasks/05-15-or-ci-pytest-cli-acceptance/prd.md` — test surface.
7. `.trellis/spec/backend/index.md` — already filled by the orchestrator with project scope and file list.

## Tools Available

You are running as a Codex agent. The following MCP servers are configured for this project:

### GitNexus MCP (code knowledge graph)

The repo has been indexed (`npx gitnexus analyze`). Most nodes are Trellis Python scripts in `.trellis/scripts/`, not OR-CI source (which does not exist yet). You may not need it for this task, but it is available.

| Tool | Purpose |
|------|---------|
| `gitnexus_query` | Find execution flows by concept |
| `gitnexus_context` | 360-degree symbol view |
| `gitnexus_cypher` | Direct graph queries |

### Filesystem (primary for this task)

The PRD files in `.trellis/tasks/` are the actual source of truth. Use plain Read/Grep to pull exact quoted terms (classification enum values, field names, JSON keys) from those PRDs — do NOT paraphrase them.

## Files to Fill

### 1. `.trellis/spec/backend/directory-structure.md`

Document the `or_ci` package layout. The PRDs imply (but do not enumerate) these modules — pick names that are consistent with the PRD's CLI/contract language:

- Public data contracts (the dataclasses/TypedDicts for ModelIR, Report, etc.)
- Metadata loading and validation (JSON in, dict out, evaluation_only carve-out)
- Submission loading (import a user-provided `.py` file, locate `build_model`)
- ModelIR extraction (Gurobi → IR)
- Verifier (orchestrates the cost-scaling metamorphic check, classifies failures)
- Report serialization (write the JSON report)
- CLI (argparse, `verify` subcommand)
- Tests directory (mirror or parallel)
- Fixtures directory (handwritten BWOR-001, BWOR-002, BWOR-010)

Include:
- Concrete directory tree showing the package and tests/fixtures layout.
- One short paragraph per module explaining its single responsibility.
- Naming conventions for modules, fixture files, classification enum values.
- "Where new code goes" rules for adding more metamorphic checks later (out of v1 scope but mention how the layout supports it).
- Anti-patterns: do NOT put Gurobi imports inside metadata loaders; do NOT mix LLM code; do NOT cross-import between verifier and extractor in cycles.

### 2. `.trellis/spec/backend/data-contracts.md`

Document every data shape that crosses an OR-CI module boundary. Use the EXACT field names and enum spellings quoted in the PRDs. Sections:

- **Problem metadata JSON** — top-level fields (`id`, `problem_type`, `instance`, `metamorphic`, `evaluation_only`), with the `metamorphic.cost_scaling` sub-schema (`coefficient_paths`, `factors`, `tolerance_abs`, `tolerance_rel`) and the `evaluation_only.{answer,label}` carve-out. Include the example block from the data-contracts PRD verbatim. Add a **`metamorphic.constraint_relaxation`** subsection labelled "**2026-05-16 continuation — emerging contract**" that says the field MAY appear with similar shape (configured numeric instance paths plus a tolerance/scale parameter), but the authoritative schema will land with the constraint-relaxation implementation PRD. Do NOT invent exact field names for it.

- **Metamorphic Checks Catalog** — one row per check (`cost_scaling`, `constraint_relaxation`). Status: Phase 1a (specified) vs. 2026-05-16 continuation (emerging). For `cost_scaling`, give the full invariant, classification on violation, and what must NOT be asserted (identical variable values). For `constraint_relaxation`, document only the invariant intent ("optimal objective is weakly better after relaxation"), mark schema TBD, and note that the verifier framework must support multiple checks side-by-side.
- **Submission contract** — exact signature `def build_model(data: dict) -> gurobipy.Model`, what `data` is (the loaded metadata's `instance` subtree, NOT the whole metadata), what `build_model` must NOT receive (`evaluation_only`), side-effect rules.
- **ModelIR** — per the extractor PRD: variables (name, lb, ub, vtype), objective (sense, linear coefficients by variable name), constraints (name, sense, rhs, linear coefficients by variable name), summary counts (variables, constraints, integer variables, binary variables). Note `model.update()` requirement and the Gurobi v12 APIs used.
- **Report JSON** — required top-level fields (`problem_id`, `submission`, `status`, `classification`, `solver_status`, `model_ir_summary`, `checks`, `failures`, `possible_causes`). Make clear that passing means "no tested invariant failed", NOT "the model is correct".
- **Canonical Vocabulary** — a definitive table that the ops/quality specs MUST reference:
  - Classification enum values: `SUCCESS`, `SYNTAX_OR_RUNTIME_ERROR`, `SOLVER_STATUS_ERROR`, `RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL`, `UNSUPPORTED_MODEL_FEATURE` (any additional categories — derive only from the PRDs).
  - Objective sense names: `min`, `max`.
  - Naming rule: BWOR only, never NL4OR.
  - Problem ID format: `BWOR-NNN`.

## Important Rules

### Stay in your lane
- ONLY modify `.trellis/spec/backend/directory-structure.md` and `.trellis/spec/backend/data-contracts.md`.
- DO NOT modify any other spec file, any task file, any source file, or run git commands.
- You may read any file for analysis.

### Quote, don't paraphrase
For enum values, JSON field names, and the metadata example, copy the exact text from the implementation PRDs. The ops and quality spec tasks will rely on you to be the single source of truth.

### No invented features
v1 is Gurobi linear only. Do not document QP, NLP, multi-objective, symmetry permutation, or LLM integration as supported. If you mention them, mark them as explicit out-of-scope. **Constraint-relaxation is in-scope as an emerging 2026-05-16 continuation** but has no implementation PRD yet — describe its intent and mark its schema as TBD; do not invent field names or invariants beyond "optimal objective weakly improves after relaxation".

### Real PRD references
Every major claim should cite a PRD path, e.g. `(see .trellis/tasks/05-15-or-ci-cost-scaling-verifier/prd.md)`.

## Acceptance Criteria

- [ ] Both files have no remaining `(To be filled ...)` placeholders.
- [ ] Every classification value, JSON key, and method name matches the implementation PRDs exactly.
- [ ] `directory-structure.md` contains a concrete tree diagram and per-module responsibilities.
- [ ] `data-contracts.md` contains the four schema sections (metadata, submission, ModelIR, report) plus the Canonical Vocabulary table.
- [ ] At least one explicit anti-pattern is documented in each file.
- [ ] Each file cites at least 2 implementation PRDs by path.

## Technical Notes

- Repo path: `/Users/zhangbowen/Projects/OR/code/or-ci`
- Implementation will live in sibling repo `../or_llm_agent` per most subtask PRDs, except `05-15-or-ci-pytest-cli-acceptance/prd.md` which says "this standalone OR-CI repo" — document the discrepancy in directory-structure.md under a "Repo Location" note (do NOT try to resolve it; that is a separate decision).
- Language: write specs in English.
