# Implementation Plan

## Steps

1. Add `build_nl4opt_rater_bundle.py` using the Phase 2 safe-bundle pattern.
2. Add `build_nl4opt_label_intake.py` using the Phase 2 intake pattern with
   NL4OPT all-20 double-label semantics.
3. Generate NL4OPT bundle and intake artifacts.
4. Wire bundle/intake status into `build_human_labeling_handoff.py`.
5. Wire bundle/intake status into `build_paper_evidence_pack_readiness.py`.
6. Update roadmap/reconciliation/integration/review-sync notes to point at the
   concrete NL4OPT operations artifacts.
7. Run validation commands and inspect explicit status counts.
8. Commit notes artifacts, archive Trellis task, and commit task metadata.

## Validation Commands

Run from the notes repo with `PYTHONDONTWRITEBYTECODE=1 uv run python`:

- `experiments/packs/or-ci-labeling-operations-2026-05-26/build_nl4opt_rater_bundle.py --check`
- `experiments/packs/or-ci-labeling-operations-2026-05-26/build_nl4opt_label_intake.py --check`
- `experiments/packs/or-ci-labeling-operations-2026-05-26/build_nl4opt_label_intake.py --self-test`
- `experiments/packs/or-ci-external-sanity-nl4opt-2026-05-26/build_nl4opt_label_agreement.py --check`
- `experiments/packs/or-ci-labeling-operations-2026-05-26/build_labeling_operations_dashboard.py --check`
- `experiments/packs/or-ci-labeling-operations-2026-05-26/build_human_labeling_handoff.py --check`
- `experiments/packs/or-ci-labeling-operations-2026-05-26/build_rater_packet_leakage_audit.py --check`
- `experiments/packs/or-ci-paper-evidence-pack-2026-05-27/build_paper_evidence_pack_readiness.py --check --self-test`
- `git diff --check`

Run from the code repo before committing Trellis changes:

- `git diff --check`
- `npx gitnexus detect-changes --repo or-ci --scope all`

## Explicit Audit

Before closing:

- Confirm bundle has exactly 20 packets `E001`-`E020`.
- Confirm incoming Rater A/B sheets each have 20 blank rows.
- Confirm intake status is `pending_external_nl4opt_labels` with 0 paired
  complete labels.
- Confirm canonical NL4OPT agreement remains pending with 0 paired and 0
  adjudicated labels.
- Confirm paper evidence readiness remains `report_ready=false`.
