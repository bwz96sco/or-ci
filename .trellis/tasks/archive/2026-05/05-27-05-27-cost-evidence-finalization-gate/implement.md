# Implementation plan

1. Add `build_cost_evidence_finalization_gate.py`.
2. Generate default operator-input CSV if missing.
3. Generate JSON/Markdown gate artifacts.
4. Implement `--check` and `--self-test`.
5. Update `build_paper_evidence_pack_readiness.py` to load the gate JSON,
   include gate snapshots, and use it for the cost-throughput row.
6. Update `build_evidence_gate_smoke_report.py` to run the gate check/self-test.
7. Regenerate affected paper readiness and smoke artifacts.
8. Update roadmap/reconciliation notes with the new gate if needed.
9. Run targeted and full checks:
   - cost ledger `--check`;
   - cost finalization `--check` and `--self-test`;
   - paper readiness and execution board checks;
   - smoke check;
   - intake/receipt checks;
   - `uv run pytest`;
   - Trellis task validation;
   - GitNexus detect-changes before commit.
