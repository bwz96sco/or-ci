# Refresh Review-Synced Roadmap Notes

## Goal

Copy the user-provided Claude review into the notes vault if needed and update
the next-stage roadmap/reconciliation notes against the archived Claude review
and GPT-5.5 Pro Extended response, with an explicit cold-protocol review gate
before capstone distribution.

## Confirmed Facts

- The notes vault already contains the normalized Claude review at
  `ideas/or-ci-next-stage-claude-review-2026-05-26.md`.
- The notes vault already contains the Oracle Pro review at
  `ideas/or-ci-next-stage-oracle-pro-review-2026-05-26.md`.
- The active roadmap is
  `ideas/or-ci-next-stage-research-roadmap-2026-05-26.md`.
- The operational reconciliation is
  `ideas/or-ci-next-stage-review-reconciliation-2026-05-27.md`.
- The review sync checkpoint is
  `ideas/or-ci-next-stage-review-sync-2026-05-27.md`.
- Current execution state is evidence-blocked: cold check labels, capstone
  double labels, 50-case labels, NL4OPT labels, mutation seed review, and
  final cost fields are not complete.

## Requirements

- Preserve the Claude review as an auditable notes-vault artifact without
  inventing or modifying its substantive methodological claims.
- Treat the archived GPT-5.5 Pro Extended response as planning-review evidence
  only, not as accepted baseline experiment evidence.
- Update the active plan so Claude and Pro review requirements remain explicit:
  two independent blinded raters for all 13 capstone artifacts; 5-case cold
  check as protocol-debug evidence only; current false-accept exposures as
  candidates, not human-confirmed false accepts; frozen units/denominators;
  and report-ready claims blocked behind promoted adjudicated human labels.
- Add an explicit cold-protocol review gate between the 5-case cold-check
  intake and capstone distribution:
  - if cold labels are incomplete, capstone remains blocked;
  - if the protocol is revised, increment the protocol version and restart
    affected labels;
  - if the protocol is accepted, record the reviewer/coordinator decision
    before capstone labels are distributed.
- Do not fabricate labels, model responses, mutation outcomes, or report-ready
  claims.

## Acceptance Criteria

- [x] The notes vault has an explicit current copy/sync statement for the
  Claude review and Oracle Pro response.
- [x] The active roadmap mentions the cold-protocol review decision gate and
  keeps capstone distribution blocked until that gate is accepted.
- [x] The reconciliation/review-sync notes make clear that the next task is
  evidence collection, not more paper claims.
- [x] Validation confirms only expected notes/Trellis files changed.

## Notes

- Lightweight documentation task; PRD-only is sufficient.
