# Add cold-check dispatch brief

## Goal

Create a generated operator/rater dispatch brief for the 5-case cold protocol check so the next external human-labeling step is executable, path-safe, and validated without creating labels.

## Confirmed Facts

- The active execution board reports `pending_external_evidence_collection`
  and primary next action `complete_5_cold_check_labels`.
- The cold-check rater bundle, distribution ZIP, handoff, intake readiness
  gate, and staged incoming label CSV already exist.
- The returned cold-check labels must stage through
  `experiments/or-ci-labeling-operations-2026-05-26/cold-protocol-intake-2026-05-27/incoming-cold-check-labels.csv`.
- The self-host source blank CSV remains provenance and bundle-generation
  input, not the coordinator return target.
- Cold-check labels are protocol-debug evidence only and must not become
  evaluation evidence unless relabeled under the final frozen protocol.

## Requirements

- Add a generated cold-check dispatch brief in the labeling operations
  experiment directory.
- The brief must give the coordinator the exact send, return, stage, validate,
  and restart steps for the 5-case cold protocol check.
- The brief must include the current rater bundle directory, distribution ZIP,
  ZIP SHA-256, staged intake CSV, source blank template, leakage audit, and
  validation command.
- The brief must distinguish rater-facing files from coordinator-only files.
- The brief must keep all current evidence gates unchanged: 0 completed
  cold labels, label promotion blocked, and paper readiness false.
- The generator must support `--check` so stale or missing dispatch output is
  caught in verification.
- The task must update the active roadmap/reconciliation only if needed to
  point at the new dispatch brief.

## Acceptance Criteria

- [x] `cold-protocol-dispatch-brief-2026-05-27.md` exists and is generated
      from current cold-check handoff/intake/distribution summaries.
- [x] The brief identifies the operations-side staged incoming label CSV as
      the coordinator return target and preserves the source blank CSV as
      provenance only.
- [x] The brief contains non-claims preventing reliability, FAR, accuracy,
      label-promotion, and report-ready claims from the cold check.
- [x] `build_cold_protocol_dispatch_brief.py --check` passes.
- [x] Existing cold intake, human handoff, leakage, label promotion, paper
      readiness, and execution-board checks still pass.
- [x] Notes changes are committed.
- [x] Trellis archive is committed.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 uv run python build_cold_protocol_dispatch_brief.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_human_labeling_handoff.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_cold_protocol_intake.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_rater_packet_leakage_audit.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_label_promotion_readiness.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_labeling_operations_dashboard.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_paper_evidence_pack_readiness.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python build_next_stage_execution_board.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m py_compile build_cold_protocol_dispatch_brief.py build_human_labeling_handoff.py build_cold_protocol_intake.py`
- `git diff --check`

## Notes Commit

- `5cc50d6 Add cold protocol dispatch brief`

## Out Of Scope

- Do not create, infer, or adjudicate human labels.
- Do not promote staged labels into canonical agreement inputs.
- Do not change baseline responses, mutation seed status, NL4OPT labels, or
  report-readiness outcomes.
- Do not distribute coordinator-only maps as rater-facing artifacts.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
