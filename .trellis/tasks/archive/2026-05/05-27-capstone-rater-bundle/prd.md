# Build capstone rater bundle

## Goal

Create and validate a reviewer-facing 13-case capstone rater bundle so two
independent human raters can label all capstone packets after the cold protocol
check, without seeing coordinator maps, case IDs, agent verdicts, or previous
source-fidelity review notes.

## Requirements

- Add a deterministic notes-vault builder for a `capstone-rater-bundle`.
- Build the bundle from the existing 13 blinded capstone packet directory and
  the existing blank Rater A / Rater B label sheets.
- Include exactly 13 packet Markdown files, one blank Rater A CSV, one blank
  Rater B CSV, a safe in-bundle manifest, a summary JSON, and a README.
- Use only in-bundle relative paths in the bundle manifest and README.
- Exclude coordinator-only packet maps, case IDs, raw artifact paths, agent
  verdicts, prior source-fidelity reviewer notes, adjudication decisions,
  baseline responses, mutation artifacts, and paper-ready claims.
- Preserve current evidence state: do not fill human labels, adjudicate labels,
  change agreement summaries, or treat cold-check labels as evaluation
  evidence.
- Update handoff/report-readiness notes to point to the safe capstone rater
  bundle while keeping the final report blocked behind missing human labels.

## Acceptance Criteria

- [x] `build_capstone_rater_bundle.py --check` passes.
- [x] The generated bundle contains 13 packet Markdown files, two blank rater
      label CSVs, one manifest, one summary JSON, and one README.
- [x] Bundle manifest and README list only safe in-bundle relative paths.
- [x] Existing labeling dashboard, human-labeling handoff, leakage audit, and
      paper evidence-pack readiness checks still pass.
- [x] Capstone agreement remains incomplete: 0 completed labels, no
      adjudicated final labels, and `report_ready=false`.
- [x] No human labels, adjudication decisions, baseline responses, mutation
      outcomes, or paper-ready claims are created.
- [x] Notes changes are committed; Trellis task is archived after verification.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
