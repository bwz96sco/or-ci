# Implementation plan

1. Add draft builder with deterministic JSON/Markdown rendering.
2. Implement source loading and validation from:
   - paper readiness CSV/JSON;
   - next-stage execution board JSON.
3. Implement `--check` and `--self-test`.
4. Generate draft artifacts.
5. Wire draft check/self-test into evidence-gate smoke.
6. Regenerate smoke artifacts.
7. Run verification:
   - draft `--check` and `--self-test`;
   - paper readiness and execution-board checks;
   - smoke check;
   - `uv run pytest`;
   - Trellis validation;
   - GitNexus detect-changes before commit.
