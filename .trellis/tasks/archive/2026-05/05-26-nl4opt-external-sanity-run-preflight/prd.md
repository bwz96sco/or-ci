# NL4OPT external sanity run preflight

## Goal

Preflight and, if ready, execute the frozen 20-case NL4OPT external sanity-check run without prompt or rubric tuning.

## User Value

The roadmap now has a frozen NL4OPT external sample. The next useful progress
is to determine whether the OR-LLM-Agent environment is ready to execute that
sample and, if it is ready, produce the external run artifacts without changing
the sample, prompts, rubric, thresholds, or solver policy.

## Confirmed Facts

- The notes commit `33f4476` created the frozen NL4OPT scaffold.
- The runbook is
  `/Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/or-ci-external-sanity-nl4opt-2026-05-26/external-sanity-nl4opt-runbook-2026-05-26.md`.
- The clean dataset is
  `/Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/or-ci-external-sanity-nl4opt-2026-05-26/external-sanity-nl4opt-dataset-20case.jsonl`.
- The selected case IDs are frozen in
  `/Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/or-ci-external-sanity-nl4opt-2026-05-26/external-sanity-nl4opt-case-ids.txt`.
- The run should be launched from
  `/Users/zhangbowen/Projects/OR/code/or_llm_agent`.
- The target artifact root is
  `/Users/zhangbowen/Projects/OR/code/or-ci/artifacts/pilot/external-sanity-nl4opt-20case-2026-05-26`.

## Requirements

- Run `uv run or-llm-agent health --agent` from the OR-LLM-Agent repo.
- Confirm the frozen dataset, statements directory, and selected IDs exist
  before any generation starts.
- If health/preflight fails, record the blocker and do not mutate prompts or
  create replacement samples.
- If health/preflight passes, run the exact frozen `solve-batch --mode agent`
  command from the runbook.
- If solve-batch completes, run the exact frozen
  `review-fidelity-batch --mode agent` command from the runbook.
- Record generated artifact locations and high-level status in the notes vault.
- Keep NL4OPT external outputs separate from BWOR metrics.

## Acceptance Criteria

- [x] Health/preflight command has been run and its result is recorded.
- [x] Dataset path, statement path, selected IDs, and artifact root have been
      checked before generation.
- [x] If execution is possible, `solve-batch` writes an artifact root with
      `summary.json` and/or clear per-case status artifacts.
- [x] If fidelity review is possible, `review-fidelity-batch` writes review
      artifacts or records a clear blocker.
- [x] No prompt, rubric, threshold, solver-policy, case-selection, or dataset
      changes are made during this task.
- [x] The notes vault records whether the task reached completed run,
      partial run, or blocked preflight state.
- [x] The code repo remains free of OR-CI package code changes unless a
      separately justified bug fix is required.

## Out of Scope

- Creating human labels for NL4OPT.
- Adjudicating external source-fidelity labels.
- Computing external FAR or accuracy claims.
- Pooling NL4OPT with BWOR headline metrics.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
