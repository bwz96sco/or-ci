# Harden cold dispatch promotion state

## Goal

Make cold protocol dispatch brief validation tolerate later label-promotion-ready states after returned labels advance, without weakening current no-label checks or report_ready=false guardrails.

## Requirements

- TBD

## Acceptance Criteria

- [ ] TBD

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
# Harden Cold Dispatch Promotion State

## Goal

Keep `build_cold_protocol_dispatch_brief.py --check` valid after later label
intake and label promotion gates advance, while preserving its current
no-label dispatch behavior and non-claim guardrails.

## Confirmed Facts

- The cold dispatch brief already tolerates the execution board advancing after
  cold labels complete.
- It still rejects any non-empty `ready_dataset_ids` and any label-promotion
  status other than `blocked_pending_complete_intake_labels`.
- That is correct for the current no-label state but brittle after any staged
  label set becomes ready for promotion.

## Requirements

- Accept `blocked_pending_complete_intake_labels` with no ready datasets.
- Accept `ready_for_label_promotion` only when ready datasets exist and blocked
  datasets are empty.
- Continue rejecting impossible label-promotion mismatches.
- Keep current generated dispatch brief behavior unchanged except as required
  by validation wording.
- Keep `report_ready=false`; do not create labels, promote labels, or make
  source-fidelity/FAR/baseline/mutation/external claims.

## Acceptance Criteria

- [ ] `build_cold_protocol_dispatch_brief.py --self-test` covers current and
  promotion-ready future states.
- [ ] `build_cold_protocol_dispatch_brief.py --check` passes.
- [ ] Paper readiness and next-stage execution board checks still pass and
  report `report_ready=false`.
- [ ] Diff checks pass in both repos.
