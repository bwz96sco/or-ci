# Refresh execution board distribution proofs

## Goal

Update the next-stage execution board so Phase 2 and NL4OPT parallel tracks
point to the deterministic sendable ZIP packages and coordinator dispatch
briefs, not only to source bundle directories.

## Confirmed Facts

- Phase 2 and NL4OPT distribution packages were committed in notes commit
  `a67abd3`.
- The active execution board is the operator-facing surface for current next
  tasks.
- The board still lists Phase 2 and NL4OPT `proof` paths as rater bundle
  directories, which is weaker than the implemented send/stage/validate
  workflow.
- This work must not create labels, promote labels, alter baseline or mutation
  outcomes, or make report-ready claims.

## Requirements

- Update `build_next_stage_execution_board.py` so the Phase 2 and NL4OPT
  parallel-track proofs include:
  - sendable ZIP path;
  - coordinator dispatch brief;
  - distribution summary;
  - intake gate.
- Regenerate `next-stage-execution-board-2026-05-27.{json,csv,md}`.
- Keep current evidence states unchanged:
  - cold check 0/5;
  - capstone 0/13;
  - Phase 2 0/50;
  - NL4OPT 0/20;
  - label promotion 0 ready datasets;
  - report-ready false.

## Acceptance Criteria

- [x] Execution board Markdown lists Phase 2 and NL4OPT proof paths as ZIP
      packages with dispatch brief and distribution summary context.
- [x] Execution board JSON/CSV regenerate deterministically.
- [x] `build_next_stage_execution_board.py --check` passes.
- [x] Relevant upstream gates still pass.
- [x] Notes changes are committed; Trellis archive is the final code-repo
      commit for this task.

## Out Of Scope

- Do not create, infer, promote, or adjudicate human labels.
- Do not alter rater bundle contents, baseline responses, mutation state, or
  report-ready gates.
