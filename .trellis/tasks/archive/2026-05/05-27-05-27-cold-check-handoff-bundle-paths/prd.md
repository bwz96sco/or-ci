# Harden cold-check handoff bundle paths

## Goal

Make the five-case cold-check handoff point to the validated safe rater bundle
instead of only exposing the older source packet locations, so the coordinator
can distribute the right files without accidentally leaking internal paths or
using stale packet copies.

## Requirements

- Update generated cold-check handoff artifacts to expose in-bundle packet and
  label-sheet paths.
- Preserve source packet paths as coordinator provenance only, not as the
  primary distribution target.
- Validate that every in-bundle cold packet exists before writing the handoff.
- Do not create labels, modify packet content, or advance the cold protocol
  gate.
- Run the handoff, cold distribution, leakage, and readiness validators before
  committing.

## Acceptance Criteria

- [x] `human-labeling-cold-check-handoff-2026-05-27.csv` includes safe bundle
      packet paths and the in-bundle `cold-check-labels.csv` return path.
- [x] `human-labeling-handoff-2026-05-27.md` displays the in-bundle paths in
      the cold protocol check table.
- [x] `build_human_labeling_handoff.py --check` and
      `build_cold_protocol_distribution_package.py --check` pass.
- [x] Leakage/readiness gates still pass and report 0 completed cold labels.
- [x] Notes changes and Trellis archive are committed.

## Verification

- `uv run python build_human_labeling_handoff.py --check`: 5 cold-check
  packets, 229 dispatch assignments.
- `uv run python build_cold_protocol_rater_bundle.py --check`: 5 packets.
- `uv run python build_cold_protocol_distribution_package.py --check`: 12
  files, SHA-256 `395cabc2d017004cac31f9b5fe444dda8dfd7635ee4ed6123616355f1bc61847`.
- `uv run python build_cold_protocol_intake.py --check`: 5 packets, 0
  complete.
- `uv run python build_rater_packet_leakage_audit.py --check`: 88 files, 0
  high issues.
- `uv run python build_labeling_operations_dashboard.py --check`: 229
  assignments, 0 complete.
- `uv run python build_label_promotion_readiness.py --check`: 0 ready, 3
  blocked.
- `uv run python build_paper_evidence_pack_readiness.py --check`: 15 sections,
  `pending_required_evidence`.
- `uv run python build_next_stage_execution_board.py --check`: 8 rows,
  `pending_external_evidence_collection`.
- `uv run python -m py_compile build_human_labeling_handoff.py
  build_cold_protocol_intake.py build_cold_protocol_rater_bundle.py
  build_cold_protocol_distribution_package.py`: passed.
- `git diff --check` in notes repo: passed.
- `npx gitnexus detect-changes --repo or-ci --scope all`: no changes
  detected.
- Notes commit: `98ac43f Harden cold-check handoff bundle paths`.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
