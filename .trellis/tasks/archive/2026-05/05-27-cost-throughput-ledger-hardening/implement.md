# Implementation Plan

1. Inspect the existing 50-case cost/throughput generator and paper-readiness
   cost-table consumption.
2. Add deterministic ledger fields for machine-cost basis and remaining cost
   blockers.
3. Regenerate the 50-case ledger artifacts.
4. Update paper-readiness cost-table logic to consume the new summary fields.
5. Regenerate paper readiness and the next-stage execution board.
6. Run verification:
   - `uv run python build_50case_cost_throughput_ledger.py --check`
   - `uv run python build_paper_evidence_pack_readiness.py --check`
   - `uv run python build_next_stage_execution_board.py --check`
   - `uv run pytest`
   - code and notes `git diff --check`
   - `task.py validate`
   - `npx gitnexus detect-changes --repo or-ci --scope all`

Rollback point: if the ledger change risks implying unsupported dollar costs,
leave `llm_cost_usd` blank and keep the readiness gate partial with a clearer
missing-evidence explanation.
