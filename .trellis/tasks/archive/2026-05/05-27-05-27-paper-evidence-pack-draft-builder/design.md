# Guarded paper evidence-pack draft builder design

## Boundary

Add:

`experiments/packs/or-ci-paper-evidence-pack-2026-05-27/build_paper_evidence_pack_draft.py`

Generated artifacts:

- `paper-evidence-pack-draft-2026-05-27.json`
- `paper-evidence-pack-draft-2026-05-27.md`

The builder reads existing readiness and execution board artifacts. It does not
modify evidence inputs or promote anything.

## Draft Semantics

The draft is a capstone report skeleton:

- If `report_ready=false` or blockers exist, status is
  `blocked_draft_pending_required_evidence`.
- If a future state has `report_ready=true` and no blockers, status may become
  `ready_draft_for_external_review`.
- Current state must remain blocked.

Each section carries only the current allowed claim and missing evidence from
the readiness gate. Blocked sections render as placeholders.

## Branch Precommitment

The draft always includes two precommitted branches:

- Branch A: FAR-reduction claim.
- Branch B: exposure/taxonomy claim.

Both branches are blocked until the readiness row
`final_branch_decision` is ready. The builder does not choose a branch.

## Smoke

Add check and self-test to the evidence-gate smoke report after paper
readiness and execution board checks.
