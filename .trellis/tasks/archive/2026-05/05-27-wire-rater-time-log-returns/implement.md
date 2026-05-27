# Implementation Plan

1. Inspect existing rater bundle generator patterns and return-file summaries.
2. Add a shared local pattern, or minimal per-file helpers if sharing would
   create more churn than it removes, for generating time-log rows.
3. Update cold, capstone, Phase 2, and NL4OPT rater bundle generators to emit
   `human-time-log.csv` and rater-facing instructions.
4. Update distribution/dispatch/send packet generators to list the time-log
   return file as expected provenance, not as recorded evidence.
5. Regenerate affected artifacts with `uv run python ...` from the notes vault.
6. Run targeted `--check`/`--self-test` commands plus the full evidence-gate
   smoke report.
7. Verify git diffs only contain expected notes-vault and Trellis changes.
