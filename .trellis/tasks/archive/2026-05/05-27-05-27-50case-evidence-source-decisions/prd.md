# Fill 50-case evidence-source decisions

## Goal

Complete the Phase 2 50-case evidence-source coordinator decision gate so the
already generated blinded rater packets can be distributed without silently
mixing reused 82-case artifacts and dedicated 50-case reruns.

## Requirements

- Use the existing 50-case bridge and decision template in the notes vault.
- Fill all 50 `coordinator_decision`, `rerun_required`, `decision_rationale`,
  `reviewer_id`, and `decided_at` fields.
- Do not create human labels, adjudication outcomes, model responses, or rerun
  results.
- Accept only rows whose existing bridge is already labelable; otherwise mark
  rerun or repair. Current bridge evidence is expected to make all 50 rows
  labelable.
- Regenerate and validate the evidence-source readiness report.
- Update roadmap/reconciliation/current handoff artifacts that summarize this
  gate.

## Acceptance Criteria

- [x] 50/50 evidence-source decision rows are complete and valid.
- [x] `validate_50case_evidence_source_decisions.py --check` passes and reports
      0 pending decisions.
- [x] Cross-track handoff/dashboard artifacts reflect the completed decision
      gate.
- [x] Paper evidence-pack readiness reflects the completed decision gate while
      preserving human-label blockers.
- [x] No human labels, model responses, mutation decisions, or rerun artifacts
      are created.
- [x] Notes repo is clean after commit.
- [x] Trellis task is archived after verification.

## Notes

- This task authorizes packet distribution only. It does not produce
  source-fidelity metrics.
