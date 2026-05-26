# Build capstone label intake gate

## Goal

Add a deterministic capstone label intake gate for the 13-case rater bundle so
returned Rater A / Rater B label sheets can be staged, validated, and reported
without changing canonical agreement outputs or creating human-label evidence
before the cold protocol check passes.

## Requirements

- Add a notes-vault builder for `capstone-label-intake-readiness`.
- Create a staging directory for incoming capstone label sheets initialized
  from the safe capstone bundle's blank Rater A / Rater B CSVs.
- Validate staged Rater A / Rater B sheets against the v2 source-fidelity label
  schema, packet IDs `P001`-`P013`, expected rater IDs, allowed enumerations,
  duplicate/missing rows, and partial-row rejection.
- Read the cold-protocol intake summary and block capstone intake advancement
  until the cold check reaches protocol-review readiness.
- Produce CSV, JSON, and Markdown readiness artifacts with per-packet state,
  rater completion counts, paired completion count, issue count, and explicit
  non-claims.
- Wire the capstone intake status into the human-labeling handoff and paper
  evidence-pack readiness snapshots.
- Preserve current evidence state: do not copy staged labels into canonical
  source label sheets, do not adjudicate labels, do not update agreement
  metrics as if labels exist, and do not make paper-ready claims.

## Acceptance Criteria

- [x] `build_capstone_label_intake.py --check` passes.
- [x] The generated intake staging directory contains blank incoming Rater A
      and Rater B CSVs with 13 rows each.
- [x] Current readiness status is blocked or pending because the cold check is
      not complete and no staged capstone labels exist.
- [x] Partial staged labels are rejected by a self-test or equivalent
      validation path.
- [x] Existing capstone bundle, cold intake, labeling dashboard, handoff,
      label agreement, leakage audit, and paper evidence-pack readiness checks
      still pass.
- [x] Capstone agreement remains incomplete: 0 paired labels, 0 adjudicated
      labels, and paper `report_ready=false`.
- [x] No human labels, adjudication decisions, baseline responses, mutation
      outcomes, or paper-ready claims are created.
- [x] Notes changes are committed; Trellis task is archived after verification.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
