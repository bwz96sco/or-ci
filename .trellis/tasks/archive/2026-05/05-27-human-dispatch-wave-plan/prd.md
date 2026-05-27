# Add human dispatch wave plan

## Goal

Add a generated human-dispatch wave plan for the OR-CI next-stage evidence
collection queue. The plan should translate the existing tracker/dashboard
state into operator waves: send now, send in parallel, hold behind cold-review,
and post-return validation steps.

## Requirements

- Place the builder and generated artifacts in the notes vault under the
  labeling-operations experiment, because this is human-evidence operations
  coordination rather than core OR-CI verifier code.
- Read existing generated truth from the human evidence tracker, labeling
  dashboard summary, paper readiness gate, and next-stage execution board. Do
  not read the evidence gate smoke report from this builder, because the smoke
  runner should validate the wave plan without creating a dependency cycle.
- Produce deterministic JSON and Markdown artifacts:
  `human-dispatch-wave-plan-2026-05-27.{json,md}`.
- Group rows into dispatch waves:
  - primary cold protocol check to send first,
  - parallel-ready Phase 2, NL4OPT, and mutation seed review work,
  - blocked capstone/cold-review follow-up work,
  - report/output gates that must remain blocked.
- For each wave, include sendable package, package hash when available,
  dispatch artifact, staging/return target, validation command, expected and
  completed counts, blocker, gate to open, and non-claim guardrail.
- Expose summary fields for primary wave, ready parallel tracks, blocked
  tracks, paper/report readiness, and total pending direct human assignments.
- Support `--check` so CI/operator runs fail when generated artifacts are
  stale or source gates are inconsistent.
- Preserve non-claim boundaries: the artifact may coordinate dispatch but must
  not create labels, mark labels complete, promote labels, accept mutation
  seeds, or advance paper readiness.

## Acceptance Criteria

- [ ] A new builder script generates JSON and Markdown dispatch-wave artifacts.
- [ ] The generated JSON includes wave rows plus summary fields for primary,
      parallel, blocked, and report-ready state.
- [ ] The Markdown names the immediate primary task and parallel-safe tasks in
      a concise operator-facing form.
- [ ] `--check` validates committed artifacts and fails on stale output or
      impossible source state.
- [ ] Existing evidence gate smoke report and core labeling/paper checks still
      pass.

## Notes

- This does not unblock the plan by itself. It reduces handoff ambiguity while
  the real blocker remains external human labels and protocol review.
