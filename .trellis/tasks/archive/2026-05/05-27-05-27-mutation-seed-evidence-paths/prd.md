# Repair mutation seed evidence paths

## Goal

Fix mutation seed manifest/review artifacts so OR-CI report paths point at existing per-case report files before human seed review and mutation work-queue eligibility.

## Requirements

- Fix mutation seed path generation so `or_ci_report_path` resolves to the
  existing per-case report file under each selected seed's artifact directory.
- Regenerate affected mutation seed artifacts and downstream review/work-queue
  artifacts that carry the report path.
- Add validation so stale or missing seed `problem_spec_path`,
  `or_ci_report_path`, and `artifact_dir` values fail checks instead of
  silently reaching human seed review.
- Preserve current human-review state: do not accept/reject seeds, enable
  mutation rows, generate mutants, or change equivalent-mutant decisions.

## Acceptance Criteria

- [x] Every mutation seed row has an existing `artifact_dir`,
      `problem_spec_path`, and `or_ci_report_path`.
- [x] Mutation seed manifest, seed review template/readiness, and mutation
      work queue are regenerated consistently.
- [x] Mutation generation remains blocked with 0 accepted seeds and 0
      run-eligible rows.
- [x] Mutation seed and work-queue checks pass.
- [x] No human labels, seed decisions, mutation outcomes, model responses, or
      baseline decisions are created.
- [x] Notes changes are committed; Trellis task is archived after verification.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- This is a PRD-only lightweight repair task.
