# Implementation Plan

1. Add the returned time-log staging helper with dry-run, execute, check, and
   self-test modes.
2. Correct the cold rater time-log template role from `cold_rater` to
   `second_rater`.
3. Update cold, capstone, Phase 2, and NL4OPT send/dispatch surfaces to mention
   the helper after returned time logs arrive.
4. Regenerate affected bundles, distributions, dispatch/send packets, human
   tracker/dispatch surfaces, paper readiness, cost operator packet, and smoke
   report.
5. Run targeted helper checks/self-tests plus full evidence-gate smoke.
6. Confirm event CSV remains header-only and report-ready remains false.
