# Add cold-check staged intake file

## Goal

Make the cold protocol check use an operations-side staged intake file, matching
the capstone, Phase 2, and NL4OPT intake patterns. Returned rater labels should
be staged under `or-ci-labeling-operations-2026-05-26/`, not written directly
into the older source blank CSV in the self-host experiment directory.

## Requirements

- Add a deterministic `cold-protocol-intake-2026-05-27/` staging directory
  with `incoming-cold-check-labels.csv`.
- Keep the staged file blank until a human rater returns labels; do not create
  or infer labels.
- Keep the source blank CSV available for provenance and bundle generation.
- Update cold intake readiness artifacts and human handoff summaries to point
  to the staged intake location.
- Preserve current status: `pending_cold_labels`, 0 completed debug labels,
  no report-ready or reliability claim.
- Run cold intake, handoff, bundle/distribution, leakage, paper-readiness, and
  execution-board validators before committing.

## Acceptance Criteria

- [x] `cold-protocol-intake-2026-05-27/incoming-cold-check-labels.csv` exists
      and is a blank staged copy for the five cold packets.
- [x] `build_cold_protocol_intake.py --check` validates the staged file, not
      the source blank CSV.
- [x] `cold-protocol-intake-readiness-2026-05-27.{csv,json,md}` exposes the
      staged intake path and still reports 0 completed labels.
- [x] `human-labeling-handoff-2026-05-27.md` and
      `human-labeling-gate-summary-2026-05-27.json` point coordinators to the
      staged intake file.
- [x] Notes changes are committed.
- [ ] Trellis archive is committed.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 uv run python build_cold_protocol_intake.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_cold_protocol_intake.py --self-test`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_cold_protocol_rater_bundle.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_cold_protocol_distribution_package.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_human_labeling_handoff.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_rater_packet_leakage_audit.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_labeling_operations_dashboard.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_label_promotion_readiness.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m py_compile build_cold_protocol_intake.py build_cold_protocol_rater_bundle.py build_human_labeling_handoff.py build_cold_protocol_distribution_package.py`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_paper_evidence_pack_readiness.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_next_stage_execution_board.py --check`
- `git diff --check`

## Notes Commit

- `2ff7054 Add cold protocol staged intake file`

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
