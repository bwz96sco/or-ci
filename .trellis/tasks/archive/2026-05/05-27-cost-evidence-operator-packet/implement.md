# Implementation plan

1. Inspect existing cost finalization gate and smoke patterns.
2. Add cost evidence operator packet builder with deterministic JSON/Markdown,
   `--check`, and `--self-test`.
3. Generate operator packet artifacts.
4. Wire packet check/self-test into evidence-gate smoke.
5. Regenerate smoke artifacts.
6. Run:
   - cost finalization `--check` and `--self-test`;
   - operator packet `--check` and `--self-test`;
   - paper readiness, execution board, and paper draft checks;
   - smoke `--check`;
   - `uv run pytest`;
   - Trellis validation;
   - GitNexus detect-changes before commit.
