# Build labeling operations dashboard

## Goal

Create a cross-experiment labeling operations dashboard and dispatch queue for capstone, 50-case, and NL4OPT human-rater work without fabricating labels.

## Confirmed Facts

- Three independent labeling tracks are currently prepared:
  - 13-case capstone: 13 packets, 100% double-label requirement, plus a 5-packet cold protocol check.
  - 50-case pilot: 50 packets, 25 planned double-label rows and 25 planned single-label rows.
  - NL4OPT external sanity check: 20 packets, 100% double-label requirement.
- Existing per-track agreement analyzers validate rater sheets and currently
  report `pending_labels`.
- Coordinator-only packet maps contain case IDs/evidence paths and must not be
  given to raters.
- This task should produce operational bookkeeping only; it must not fill,
  infer, or adjudicate any human label.

## Requirements

- Add a cross-experiment labeling operations builder under a dedicated notes
  experiment directory.
- Generate a dispatch queue with one row per required rater/adjudicator action.
- Include packet paths, label-sheet paths, dependencies, status, and blockers
  without exposing coordinator-only packet maps as rater-facing files.
- Summarize current completion counts across capstone, cold check, 50-case, and
  NL4OPT labeling tracks.
- Validate that packet files, rater sheets, adjudication sheets, and per-track
  agreement summaries exist and remain consistent with the generated dispatch
  queue.
- Update the roadmap/integration note so the next human-labeling action points
  at the operations dashboard.

## Acceptance Criteria

- [x] A dashboard builder script exists and runs with `uv run python`.
- [x] Generated dispatch queue includes every required cold-rater, rater A,
      rater B, and adjudicator assignment.
- [x] Generated summary reports zero completed human labels in the current
      state and lists the human-rater blocker explicitly.
- [x] `--check` validates generated outputs against source packet/rater files.
- [x] Existing capstone, 50-case, and NL4OPT label agreement checks still pass.
- [x] `uv run pytest` for OR-CI still passes.
- [x] Roadmap status is updated without claiming labeling completion.

## Out of Scope

- Recruiting raters or assigning named people.
- Filling rater labels, adjudication labels, or timestamps.
- Computing agreement metrics before labels exist.
- Changing packet contents or revealing coordinator-only maps to raters.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
