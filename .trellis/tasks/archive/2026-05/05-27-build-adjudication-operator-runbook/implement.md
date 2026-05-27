# Implementation Plan

1. Add the generated adjudication runbook builder with `--check` and
   `--self-test`.
2. Build rows for capstone, Phase 2, and NL4OPT from current promotion/intake
   sources.
3. Generate JSON/CSV/Markdown artifacts.
4. Add the runbook check and self-test to the evidence-gate smoke report.
5. Regenerate smoke/report artifacts.
6. Verify smoke, runbook checks, paper readiness, pytest, and GitNexus before
   committing.
