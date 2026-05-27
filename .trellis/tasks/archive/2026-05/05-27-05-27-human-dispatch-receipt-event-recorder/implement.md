# Implementation Plan

1. Add `record_human_dispatch_receipt_event.py` in the labeling-operations
   experiment directory.
2. Reuse the existing wave-plan and receipt-events schema constants where
   possible; keep the recorder independent from generated ledger writes.
3. Implement non-mutating modes:
   - default dry-run preview;
   - `--check` to validate current events without rewriting;
   - `--self-test` over temporary in-memory / temporary-file scenarios.
4. Implement explicit mutating mode:
   - `--execute --event sent ...`;
   - `--execute --event returned ...`.
5. Wire recorder self-test into `build_evidence_gate_smoke_report.py`.
6. Regenerate and check the smoke report.
7. Update roadmap/sync notes only for the operational pointer and command
   counts; do not change evidence counts.
8. Run validation:
   - recorder `--check` / `--self-test`;
   - dry-run preview with checksum before/after equality;
   - receipt ledger `--check`;
   - evidence smoke `--check`;
   - paper readiness / execution board `--check`;
   - `uv run pytest`;
   - Trellis task validate;
   - GitNexus detect changes before code-repo commit.
