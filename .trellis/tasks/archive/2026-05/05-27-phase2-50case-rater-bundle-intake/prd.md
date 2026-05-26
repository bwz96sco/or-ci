# Build 50-case rater bundle intake

## Goal

Create safe distribution and intake tooling for the Phase 2 50-case pilot so
Rater A and Rater B can receive the selected packets and return staged labels
without seeing coordinator manifests, case IDs, raw artifact paths, previous
source-fidelity reviewer notes, or paper-claim framing.

## Requirements

- Add deterministic notes-vault builders for:
  - a safe `phase2-50case-rater-bundle`;
  - a `phase2-50case-label-intake-readiness` gate.
- Build the bundle from existing 50-case blinded packet files, packet index,
  label manifest, blank Rater A label sheet, and blank Rater B label sheet.
- Include exactly 50 packet Markdown files, a 50-row blank Rater A CSV, a
  25-row blank Rater B CSV for planned double-label cases, a safe in-bundle
  manifest, summary JSON, and README.
- Use only in-bundle relative paths in the bundle manifest and README.
- Exclude coordinator-only maps, BWOR case IDs, raw artifact paths, prior LLM
  source-fidelity reviewer verdicts, adjudication decisions, baseline
  responses, mutation artifacts, and paper-ready claims.
- Initialize a staging directory for returned Rater A / Rater B label sheets
  from the safe bundle.
- Validate staged label sheets against the v2 schema, expected packet sets,
  rater IDs, allowed enumerations, duplicate/missing rows, and partial-row
  rejection.
- Report intake readiness with per-packet state, Rater A/B completion counts,
  planned double-label paired-complete count, issue count, and explicit
  non-claims.
- Wire the 50-case bundle and intake status into the human-labeling handoff and
  paper evidence-pack readiness snapshots.
- Preserve current evidence state: do not copy staged labels into canonical
  50-case label sheets, do not adjudicate labels, do not update agreement
  metrics as if labels exist, and do not make paper-ready claims.

## Acceptance Criteria

- [x] `build_phase2_50case_rater_bundle.py --check` passes.
- [x] `build_phase2_50case_label_intake.py --check` and `--self-test` pass.
- [x] The generated bundle contains 50 packet Markdown files, blank Rater A
      and Rater B CSVs, one manifest, one summary JSON, and one README.
- [x] The generated intake staging directory contains blank incoming Rater A
      and Rater B CSVs with 50 and 25 rows respectively.
- [x] Current intake readiness remains pending, with 0 Rater A complete, 0
      Rater B complete, 0 paired double-labels complete, and no paper-ready
      claims.
- [x] Existing 50-case agreement analyzer, labeling dashboard, human-labeling
      handoff, leakage audit, and paper evidence-pack readiness checks still
      pass.
- [x] No human labels, adjudication decisions, baseline responses, mutation
      outcomes, or source-fidelity accuracy/FAR claims are created.
- [x] Notes changes are committed; Trellis task is archived after verification.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
