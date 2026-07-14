# Implementation Plan

## Steps

1. Add `build_label_promotion_readiness.py`.
2. Generate promotion readiness artifacts.
3. Wire promotion readiness into `build_human_labeling_handoff.py`.
4. Wire promotion readiness into `build_paper_evidence_pack_readiness.py`.
5. Update roadmap/reconciliation notes with the promotion gate.
6. Run validation and explicit no-copy audit.
7. Commit notes and archive this Trellis task.

## Validation Commands

Run from the notes repo:

- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-labeling-operations-2026-05-26/build_label_promotion_readiness.py`
- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-labeling-operations-2026-05-26/build_label_promotion_readiness.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-labeling-operations-2026-05-26/build_label_promotion_readiness.py --dataset capstone_13 --execute` should fail while labels are pending.
- Existing intake, handoff, dashboard, leakage, and paper readiness checks.
- `git diff --check`

Run from the code repo before committing Trellis:

- `git diff --check`
- `npx gitnexus detect-changes --repo or-ci --scope all`

## Explicit Audit

- Confirm canonical capstone, Phase 2, and NL4OPT rater CSVs remain unchanged.
- Confirm promotion readiness reports all datasets as not promotion-ready.
- Confirm paper evidence pack remains `report_ready=false`.
