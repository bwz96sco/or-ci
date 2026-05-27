# Implementation plan

1. Inspect existing wave plan, receipt ledger, receipt recorder, intake gates,
   and smoke report patterns.
2. Add `build_human_dispatch_outbox_preflight.py` with deterministic source
   loading, package checks, target checks, JSON/CSV/Markdown rendering,
   `--check`, and `--self-test`.
3. Generate preflight artifacts.
4. Wire preflight check/self-test into the evidence-gate smoke report.
5. Regenerate smoke artifacts.
6. Run verification:
   - outbox preflight `--check` and `--self-test`;
   - receipt ledger check;
   - cold, phase2, NL4OPT, and mutation intake/readiness checks;
   - paper evidence-gate smoke check;
   - `uv run pytest`;
   - Trellis task validation;
   - GitNexus detect-changes before commit.
