# Implementation Plan

1. Inspect existing mutation queue, applicability, backlog, and plan-preview
   scripts for shared helpers and file naming conventions.
2. Add `generate_mutation_artifacts.py` to the self-host exploration experiment.
3. Generate `mutation-generation-records-2026-05-26.csv`,
   `mutation-generation-records-2026-05-26.json`, and
   `mutation-generation-records-summary-2026-05-26.md` from the current queue.
4. Add `--check` validation that:
   - confirms generated records are fresh;
   - confirms current real rows produce zero mutated artifacts;
   - validates planned values match seed specs before any future write;
   - runs a temporary self-test for one synthetic eligible P0/P1 row.
5. Update the roadmap/integration note status to record the generator stage as
   implemented, while keeping actual mutation runs blocked pending trusted seed
   acceptance.
6. Run validation:
   - `uv run python build_mutation_work_queue.py --check`
   - `uv run python build_mutation_applicability.py --check`
   - `uv run python build_mutation_plan_preview.py --check`
   - `uv run python generate_mutation_artifacts.py --check`
   - `uv run pytest`
7. Commit notes changes, then archive the Trellis task and commit the Trellis
   archive.
