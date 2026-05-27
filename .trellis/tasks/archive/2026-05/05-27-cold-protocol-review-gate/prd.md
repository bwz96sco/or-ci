# Implement Cold Protocol Review Gate

## Goal

Add a generated cold-protocol review decision gate to the notes-vault labeling
operations so capstone distribution, capstone label intake, paper readiness,
and the execution board are blocked until a complete cold-check intake is
followed by an explicit `accept_protocol` decision.

## Confirmed Facts

- The active roadmap now requires a post-cold-check decision:
  `accept_protocol`, `revise_protocol`, or `keep_blocked`.
- Existing generated gates only read
  `cold-protocol-intake-readiness-2026-05-27.json`; they do not yet require a
  separate protocol-review decision artifact.
- Current cold intake is `pending_cold_labels` with 0/5 completed debug labels.
- Current capstone distribution and label intake are blocked only by the cold
  intake status.
- Human labels, model outputs, mutation outcomes, and report-ready evidence
  must not be fabricated.

## Requirements

- Create an operations-side cold-protocol review gate builder in the notes
  vault that:
  - owns a staged coordinator decision CSV;
  - initializes the decision CSV without inventing a decision;
  - validates `review_decision` as exactly one of blank,
    `accept_protocol`, `revise_protocol`, or `keep_blocked`;
  - requires reviewer/coordinator id, review date, rationale, and protocol
    version when a decision is present;
  - reports `blocked_pending_cold_labels` until cold intake is
    `ready_for_protocol_review`;
  - reports `blocked_pending_protocol_review_decision` when cold labels are
    complete but the decision is blank;
  - reports `ready_for_capstone_distribution` only when the decision is
    `accept_protocol`;
  - reports `blocked_protocol_revision_required` for `revise_protocol` and
    `blocked_by_protocol_review` for `keep_blocked`;
  - preserves non-claims that the cold check is protocol-debug evidence only.
- Wire the new gate into:
  - capstone distribution package status and send brief;
  - capstone label intake status;
  - human labeling handoff summary;
  - paper evidence-pack readiness gate;
  - next-stage execution board.
- Keep current generated outputs consistent with the present state: no cold
  labels, blank protocol decision, capstone blocked, paper `report_ready=false`.
- Use existing local builder style, deterministic JSON/CSV/Markdown outputs,
  and `--check` validation.

## Acceptance Criteria

- [x] `build_cold_protocol_review_gate.py --check` validates generated CSV,
  JSON, and Markdown artifacts.
- [x] Capstone distribution remains blocked with a blocker that references both
  cold labels and protocol review.
- [x] Capstone label intake remains blocked until the review gate is
  `ready_for_capstone_distribution`.
- [x] Paper readiness and execution board include the cold-protocol review
  gate in their proof artifacts and next actions.
- [x] Existing validators for cold intake, capstone distribution/intake, human
  handoff, paper readiness, and execution board pass.
- [x] No labels, model responses, mutation outcomes, or report-ready claims are
  created.

## Notes

- This is infrastructure for an existing research plan, not a substitute for
  external human labels.
