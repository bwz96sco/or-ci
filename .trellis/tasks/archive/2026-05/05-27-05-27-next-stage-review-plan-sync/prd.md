# Sync next-stage review plan notes

## Goal

Keep the OR-CI next-stage research-plan notes internally consistent after the
Claude methodological review, the GPT-5.5 Pro Extended Oracle review, and the
completed 52/52 Extended Pro baseline-response capture.

## Requirements

- Preserve the archived Claude review and Oracle Pro review as external
  planning evidence in the notes vault.
- Update stale plan text that still describes the baseline-response track as
  pending model submission or blocked by the old P001/P010 browser failures.
- Keep the active roadmap aligned with the current execution board:
  external human evidence remains the primary blocker, and baseline work is
  complete only through raw-response capture, not performance claims.
- Do not create or imply human labels, adjudication results, mutation
  outcomes, external-validity claims, or report-ready status.
- Leave `.trellis/workspace` and unrelated user changes untouched.

## Acceptance Criteria

- [x] Notes-vault plan files mention the copied Claude and Oracle Pro review
      inputs and the updated 52/52 baseline-response status consistently.
- [x] The next task remains the 5-case cold protocol check, followed by
      capstone double labeling, 50-case/NL4OPT labels, mutation seed review,
      and the final evidence pack only after evidence gates pass.
- [x] Notes-side readiness/check scripts pass without regenerating unexpected
      content.
- [x] GitNexus detect-changes is run before any code/Trellis commit.
- [x] Notes changes and Trellis archive are committed separately if needed.

## Verification

- `build_labeling_operations_dashboard.py --check`: 229 assignments, 0 complete.
- `build_cold_protocol_intake.py --check`: 5 packets, 0 complete.
- `build_rater_packet_leakage_audit.py --check`: 88 files, 0 high issues.
- `build_label_promotion_readiness.py --check`: 0 ready, 3 blocked.
- `build_capstone_label_intake.py --check`: blocked pending cold protocol check.
- `build_phase2_50case_label_intake.py --check`: 0 double-label pairs complete.
- `build_nl4opt_label_intake.py --check`: 0 paired complete.
- `build_baseline_response_operator_queue.py --check`: 52 rows,
  `baseline_response_capture_complete_pending_results_and_labels`.
- `build_baseline_response_intake.py --check`: 52 expected, 0 promotable.
- `build_baseline_response_capture.py --check`: 52 expected, 52 present.
- `build_baseline_ablation_results.py --check`: 52 completed, 0 pending.
- `build_mutation_seed_review_operator_queue.py --check`: 29 rows,
  `pending_human_seed_reviews`.
- `build_mutation_seed_review_intake.py --check`: 29 seeds, 0 promotable.
- `build_mutation_seed_review.py --check`: 29 seeds, 0 accepted.
- `build_paper_evidence_pack_readiness.py --check`: 15 sections,
  `pending_required_evidence`.
- `build_next_stage_execution_board.py --check`: 8 rows,
  `pending_external_evidence_collection`.
- `npx gitnexus detect-changes --repo or-ci --scope all`: no changes detected.
- Notes commit: `08b2a0b Sync next-stage review integration status`.
- Trellis archive committed as `chore(task): archive 05-27-05-27-next-stage-review-plan-sync`.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
