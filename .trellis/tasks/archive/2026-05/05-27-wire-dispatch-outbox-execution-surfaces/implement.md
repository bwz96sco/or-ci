# Implementation plan

1. Add outbox preflight as a required source in the human tracker.
2. Add outbox counts/status map to tracker JSON and Markdown.
3. Add outbox preflight as a required source in the execution board.
4. Add outbox counts/status and proof references to board JSON/Markdown.
5. Regenerate dependent artifacts.
6. Run:
   - tracker `--check`;
   - wave plan `--check`;
   - receipt ledger `--check`;
   - outbox preflight `--check`;
   - execution board `--check` and `--self-test`;
   - paper draft `--check`;
   - smoke `--check`;
   - `uv run pytest`;
   - Trellis validation;
   - GitNexus detect-changes before commit.
