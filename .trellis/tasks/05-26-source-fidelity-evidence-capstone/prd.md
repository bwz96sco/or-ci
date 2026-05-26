# Source fidelity evidence capstone

## Goal

Run the structured source-fidelity rubric/capstone workflow on existing OR-LLM-Agent batch evidence and update the research report output with clear accepted/rejected/provisional counts and claim boundaries.

Target evidence root:

`/Users/zhangbowen/Projects/OR/code/or-ci/artifacts/pilot/or-llm-agent-full-bwor-2026-05-25`

Target report directory:

`/Users/zhangbowen/Projects/OR/note/OR-research/experiments/or-ci-self-host-exploration-2026-05-25`

## Requirements

- Run the new `source_fidelity_v1` review/capstone workflow on the latest full 82-case OR-LLM-Agent batch root.
- Use a bounded high-value review set rather than launching 82 nested reviewers:
  - Direct/generated-spec successes: `BWOR-001`, `BWOR-016`, `BWOR-051`, `BWOR-067`, `BWOR-071`, `BWOR-082`.
  - Baseline blocked boundary cases: `BWOR-020`, `BWOR-027`, `BWOR-061`.
  - Clarified/provisional examples: `BWOR-014`, `BWOR-015`, `BWOR-027`, `BWOR-046` clarified artifacts.
- Preserve the claim boundary: OR-CI `PASS` means generated-spec/code consistency, not source-faithful success.
- Write or update report-facing artifacts in the experiment directory so the capstone can be cited without reading raw run directories.
- Update the experiment README next-task/current-state language to reflect that the structured rubric exists and now has a bounded evidence pass.

## Acceptance Criteria

- [ ] The Trellis plan for this evidence pass is archived in the task directory.
- [ ] Baseline batch root has `fidelity-rubric-summary.json` and `fidelity-rubric-report.md`.
- [ ] Selected baseline cases have updated `spec/fidelity-review.json` and `spec/fidelity-review.md`.
- [ ] Selected clarified artifacts have structured review output or are explicitly reported as not reviewed if agent review cannot run.
- [ ] Experiment directory contains a report-facing capstone summary with reviewed/rejected/provisional counts and artifact paths.
- [ ] README identifies the new strongest defensible claim and next task.
- [ ] OR-LLM-Agent tests still pass after the evidence run.

## Notes

- Do not mutate OR-CI verifier code for this task.
- Nested Codex review is part of OR-LLM-Agent's product workflow, not a Trellis implementation sub-agent.
