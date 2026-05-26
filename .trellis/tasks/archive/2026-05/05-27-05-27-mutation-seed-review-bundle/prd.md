# Build mutation seed review bundle

## Goal

Create and validate a reviewer-facing mutation seed review bundle from the 29 candidate seeds so humans can accept/reject trusted seeds without using stale raw paths or generated mutation outputs.

## Requirements

- Add a deterministic notes-vault builder for a mutation seed review bundle.
- Build the bundle from the existing mutation seed review template and existing
  seed evidence paths.
- Create one reviewer-facing packet per seed candidate. Each packet should
  contain the source statement, generated ProblemSpec, and a compact OR-CI
  generated-spec/code verification summary.
- Include a blank in-bundle seed review CSV and safe manifest using only
  in-bundle relative paths.
- Exclude coordinator-only raw artifact paths, generated mutation outputs,
  equivalent-mutant decisions, model responses, and source-fidelity reviewer
  notes.
- Preserve the current human-review state: do not accept/reject seeds, enable
  mutation rows, generate mutants, or change equivalent-mutant decisions.

## Acceptance Criteria

- [x] `build_mutation_seed_review_bundle.py --check` passes.
- [x] The generated bundle contains 29 seed packet Markdown files and one blank
      review CSV.
- [x] Bundle manifest lists only in-bundle relative paths.
- [x] Existing mutation seed review and work-queue checks still pass with 0
      accepted seeds and 0 run-eligible rows.
- [x] Paper evidence-pack readiness still reports `pending_required_evidence`
      and `report_ready=false`.
- [x] No human labels, seed decisions, mutation outcomes, model responses, or
      baseline decisions are created.
- [x] Notes changes are committed; Trellis task is archived after verification.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- This is a PRD-only lightweight support task.
