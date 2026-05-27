# Add parallel labeling distribution packages

## Goal

Generate deterministic ZIP distribution packages and coordinator dispatch briefs for the Phase 2 50-case and NL4OPT rater bundles so the parallel human-labeling tracks are sendable and stage returned labels through existing intake gates without creating labels.

## Confirmed Facts

- The execution board lists `phase2_50case_labels` and
  `nl4opt_external_labels` as parallel evidence-collection tracks.
- Both tracks already have safe rater bundle directories, staged intake
  directories, and readiness validators.
- Only the cold-check and capstone tracks currently have deterministic ZIP
  distribution packages and coordinator dispatch briefs.
- Phase 2 has 50 Rater A rows and 25 Rater B rows. NL4OPT has 20 Rater A
  rows and 20 Rater B rows.
- The work must not create labels or claim Phase 2/NL4OPT accuracy before
  returned labels and adjudication exist.

## Requirements

- Add generated deterministic ZIP distribution packages for:
  - `phase2-50case-rater-bundle-2026-05-27`
  - `nl4opt-rater-bundle-2026-05-27`
- Add generated JSON/Markdown distribution summaries for both tracks.
- Add generated coordinator dispatch briefs for both tracks that identify
  sendable ZIPs, ZIP hashes, rater return sheets, staging paths, validation
  commands, and non-claims.
- Wire the new artifacts into the human-labeling handoff and active
  roadmap/reconciliation notes.
- Preserve current evidence states: 0 Phase 2 labels, 0 NL4OPT labels,
  promotion blocked, report-ready false.
- Add `--check` validation so stale ZIPs, summaries, briefs, or source
  bundles fail deterministically.

## Acceptance Criteria

- [x] `phase2-50case-rater-bundle-2026-05-27.zip` and
      `nl4opt-rater-bundle-2026-05-27.zip` exist with deterministic summaries.
- [x] `phase2-50case-rater-bundle-distribution-2026-05-27.{json,md}` and
      `nl4opt-rater-bundle-distribution-2026-05-27.{json,md}` exist.
- [x] `phase2-50case-dispatch-brief-2026-05-27.md` and
      `nl4opt-dispatch-brief-2026-05-27.md` identify send/stage/validate
      steps and non-claims.
- [x] New distribution checker passes.
- [x] Existing Phase 2 intake, NL4OPT intake, leakage, label promotion, paper
      readiness, and execution-board checks still pass.
- [x] Notes changes are committed; Trellis archive is the final code-repo
      commit for this task.

## Out Of Scope

- Do not create, infer, promote, or adjudicate human labels.
- Do not change baseline, mutation, cold, capstone, or report-readiness
  outcomes.
- Do not claim source-fidelity accuracy, FAR reduction, or external validity
  from prepared distribution packages.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
