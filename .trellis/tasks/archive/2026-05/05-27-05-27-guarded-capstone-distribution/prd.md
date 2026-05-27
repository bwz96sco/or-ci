# Add guarded capstone distribution package

## Goal

Generate a sendable capstone rater-bundle ZIP plus coordinator dispatch brief that remains blocked until the cold protocol check is ready, so the next post-cold human-labeling step is executable without creating labels.

## Confirmed Facts

- The active execution board reports `complete_5_cold_check_labels` as the
  primary next action and `wait_for_cold_check_then_dispatch_capstone_bundle`
  as the next capstone action.
- The safe capstone rater bundle directory already exists with 13 packets,
  `rater-a-labels.csv`, and `rater-b-labels.csv`.
- There is currently a deterministic ZIP/distribution summary for the cold
  protocol bundle, but not for the capstone rater bundle.
- The capstone label intake gate is blocked until cold protocol intake reaches
  `ready_for_protocol_review`.
- Creating a ZIP and dispatch brief must not imply that the capstone can be
  sent before the cold check passes.

## Requirements

- Add a generated capstone rater-bundle distribution package:
  deterministic ZIP, JSON summary, and Markdown summary.
- Add a generated coordinator dispatch brief for the capstone bundle that
  says whether the bundle is sendable now or blocked by the cold protocol
  gate.
- The distribution package must include only rater-facing capstone bundle
  files and preserve deterministic ZIP metadata.
- The dispatch brief must include the ZIP path, SHA-256, Rater A/B return
  sheets, staged capstone intake directory, cold-check prerequisite, and
  validation commands.
- The generator must support `--check` and fail when the bundle, cold gate, or
  generated artifacts are stale.
- The human handoff and roadmap/reconciliation should point to the new
  guarded capstone distribution artifacts.
- Existing evidence gates must remain unchanged: cold labels 0/5, capstone
  paired labels 0/13, label promotion blocked, and report-ready false.

## Acceptance Criteria

- [x] `capstone-rater-bundle-2026-05-27.zip` exists and has deterministic
      summary artifacts.
- [x] `capstone-rater-bundle-distribution-2026-05-27.{json,md}` exist and
      report a blocked-by-cold-check distribution status while cold labels are
      pending.
- [x] `capstone-dispatch-brief-2026-05-27.md` identifies the ZIP, staged
      capstone intake paths, cold-check prerequisite, validation commands, and
      non-claims.
- [x] `build_capstone_distribution_package.py --check` passes.
- [x] Existing capstone bundle, capstone intake, cold intake, handoff,
      leakage, label promotion, paper readiness, and execution-board checks
      still pass.
- [x] Notes changes are committed.
- [x] Trellis archive is committed.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 uv run python build_capstone_distribution_package.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_capstone_rater_bundle.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_capstone_label_intake.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_cold_protocol_intake.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_human_labeling_handoff.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_rater_packet_leakage_audit.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_label_promotion_readiness.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_labeling_operations_dashboard.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_paper_evidence_pack_readiness.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_next_stage_execution_board.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m py_compile build_capstone_distribution_package.py build_human_labeling_handoff.py build_capstone_rater_bundle.py build_capstone_label_intake.py`
- `git diff --check`

## Notes Commit

- `6929b24 Add guarded capstone distribution package`

## Out Of Scope

- Do not create, infer, or adjudicate human labels.
- Do not mark the capstone bundle sendable before the cold protocol gate is
  ready.
- Do not promote staged labels, compute agreement metrics, or change
  report-readiness outcomes.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
