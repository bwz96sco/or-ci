# Implementation Plan

1. Add the generated runbook script with `--check` and `--self-test`.
2. Build rows from existing dispatch artifacts and hard fail if returned source
   examples are not `<returned ...>` placeholders.
3. Generate JSON/CSV/Markdown runbook artifacts.
4. Add the runbook check to the evidence-gate smoke report.
5. Regenerate paper/readiness/smoke artifacts.
6. Verify smoke, helper checks, header-only human-time event CSV, OR-CI pytest,
   and GitNexus detect-changes before committing.
