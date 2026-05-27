# Implementation plan

1. Add receipt metadata fields to `StagingTarget`.
2. Populate receipt metadata for cold protocol, mutation seed review, and
   split-label targets.
3. Add helper functions that render dry-run receipt-return commands or
   split-label notes.
4. Print the receipt bookkeeping section from `stage()`.
5. Extend `self_test()` to verify:
   - cold command includes the expected wave id and SHA;
   - mutation command includes the expected wave id and SHA;
   - split-label guidance does not include a returned-event command.
6. Run targeted notes checks:
   - `stage_returned_human_evidence.py --check`;
   - `stage_returned_human_evidence.py --self-test`;
   - representative valid dry-runs in a temporary source/target path if needed.
7. Run full gates:
   - intake checks;
   - receipt checks;
   - paper-readiness and execution-board checks;
   - evidence-gate smoke check;
   - `uv run pytest` in the code repo;
   - Trellis task validation;
   - GitNexus detect-changes before commit.
