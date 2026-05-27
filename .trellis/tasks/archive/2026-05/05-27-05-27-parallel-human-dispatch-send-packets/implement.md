# Implementation Plan

1. Add `build_parallel_human_dispatch_send_packets.py` in the labeling
   operations experiment directory.
2. Build a data model for the three parallel-safe waves from existing
   distribution/queue artifacts.
3. Validate:
   - expected wave IDs exist;
   - wave state is ready;
   - receipt-events rows are blank;
   - receipt ledger rows are unsent;
   - ZIP checksums match when a ZIP is available;
   - mutation bundle directory files exist.
4. Generate JSON and Markdown packet artifacts.
5. Add `--check` and `--self-test`.
6. Wire the new check/self-test into `build_evidence_gate_smoke_report.py`.
7. Update roadmap/sync notes to point to the parallel send packet and update
   smoke command count.
8. Run validation:
   - generator `--check` and `--self-test`;
   - receipt-event checksum unchanged;
   - receipt ledger/tracker/handoff/dashboard/paper/board checks;
   - evidence smoke check;
   - `uv run pytest`;
   - Trellis task validate;
   - GitNexus detect changes before code-repo commit.
