# Harden distribution package future states

## Goal

Make capstone, Phase 2, and NL4OPT distribution-package checks tolerate legitimate future states after returned labels exist or label promotion becomes ready, while preserving current blocked/report_ready=false behavior and non-claims.

## Requirements

- TBD

## Acceptance Criteria

- [ ] TBD

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
# Harden Distribution Package Future States

## Goal

Make generated rater-bundle distribution package checks remain valid after
labels start returning and label-promotion readiness advances. Distribution
packages should validate the package that was sent and the non-claim guardrails;
they should not fail merely because a later intake/promotion gate has moved
forward.

## Confirmed Facts

- Current capstone, Phase 2, and NL4OPT distribution checks pass in the
  no-label state.
- `build_capstone_distribution_package.py` rejects any capstone paired labels
  and any non-blocked label-promotion status.
- `build_parallel_labeling_distribution_packages.py` rejects nonzero returned
  label counts and any non-blocked label-promotion status for Phase 2/NL4OPT.
- Those checks protect the initial distribution state, but they become brittle
  once human labels are returned or staged labels become ready for promotion.
- Distribution artifacts must not become evidence of labels, agreement,
  adjudication, or paper readiness.

## Requirements

- Keep current generated outputs unchanged except for wording or metadata that
  is necessary to express current/future-state validation.
- Preserve current no-label behavior: cold pending, capstone blocked,
  Phase 2/NL4OPT sendable, `report_ready=false`.
- Allow distribution-package `--check` to pass after the corresponding intake
  gate has advanced, provided package hashes still match and `report_ready`
  remains false.
- Do not require `label-promotion-readiness` to remain
  `blocked_pending_complete_intake_labels` forever. Accept
  `ready_for_label_promotion` when ready datasets exist, while still rejecting
  impossible mismatches.
- Add self-test coverage for current no-label state and future progressed
  states for capstone and parallel distribution packages.
- Do not fabricate labels, promote staged labels, create adjudication outputs,
  or make source-fidelity/FAR/baseline/mutation/external-validity claims.

## Acceptance Criteria

- [ ] Current distribution package checks still pass.
- [ ] Capstone distribution package self-test covers blocked/current state and
  future states where capstone labels are ready for adjudication or protocol
  accepted.
- [ ] Parallel distribution package self-test covers current state and future
  returned-label / promotion-ready states for Phase 2 or NL4OPT.
- [ ] Paper readiness and next-stage board checks still report
  `report_ready=false`.
- [ ] Git diff checks pass in both repos.
