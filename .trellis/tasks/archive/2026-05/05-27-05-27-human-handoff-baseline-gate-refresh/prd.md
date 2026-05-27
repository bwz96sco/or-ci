# Refresh human handoff baseline gate

## Goal

Refresh the generated human-labeling handoff so its baseline-response gate
matches the current validated state: 52/52 Extended Pro baseline responses are
captured, while performance analysis remains blocked on adjudicated human
labels.

## Requirements

- Update the handoff generator and generated artifacts that still describe the
  baseline track as pending external model responses.
- Preserve all human-labeling blockers: no cold labels, capstone labels,
  50-case labels, NL4OPT labels, or mutation seed reviews may be invented.
- Keep the handoff focused on the current operator action order: cold check
  first; baseline action is now validation/pairing with future promoted human
  labels, not model submission.
- Keep forbidden claims intact: no baseline performance, FAR, accuracy, or
  report-ready claim before adjudicated labels and report gates pass.
- Run the relevant notes-side gate validators and GitNexus detect-changes
  before committing Trellis archive state.

## Acceptance Criteria

- [x] `human-labeling-handoff-2026-05-27.md` reports baseline capture as
      complete at 52/52 and labels as the remaining baseline blocker.
- [x] `human-labeling-gate-summary-2026-05-27.json` exposes current baseline
      capture fields instead of stale `0 staged / 0 raw` fields.
- [x] Regeneration is deterministic under `build_human_labeling_handoff.py
      --check`.
- [x] Baseline, labeling, paper-readiness, and execution-board validators pass.
- [x] Notes changes and Trellis archive are committed.

## Verification

- `uv run python build_human_labeling_handoff.py --check`: 5 cold-check
  packets, 229 dispatch assignments.
- `uv run python build_labeling_operations_dashboard.py --check`: 229
  assignments, 0 complete.
- `uv run python build_cold_protocol_intake.py --check`: 5 packets, 0
  complete.
- `uv run python build_baseline_response_operator_queue.py --check`: 52 rows,
  `baseline_response_capture_complete_pending_results_and_labels`.
- `uv run python build_baseline_response_intake.py --check`: 52 expected, 0
  promotable.
- `uv run python build_baseline_response_capture.py --check`: 52 expected, 52
  present.
- `uv run python build_baseline_ablation_results.py --check`: 52 completed, 0
  pending.
- `uv run python build_rater_packet_leakage_audit.py --check`: 88 files, 0
  high issues.
- `uv run python build_label_promotion_readiness.py --check`: 0 ready, 3
  blocked.
- `uv run python build_paper_evidence_pack_readiness.py --check`: 15 sections,
  `pending_required_evidence`.
- `uv run python build_next_stage_execution_board.py --check`: 8 rows,
  `pending_external_evidence_collection`.
- `uv run python -m py_compile build_human_labeling_handoff.py`: passed.
- `git diff --check` in notes repo: passed.
- `npx gitnexus detect-changes --repo or-ci --scope all`: no changes
  detected.
- Notes commit: `1358015 Refresh human labeling handoff baseline gate`.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
