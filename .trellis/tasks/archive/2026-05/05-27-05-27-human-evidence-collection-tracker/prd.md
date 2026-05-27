# Build Human Evidence Collection Tracker

## Goal

Create a deterministic operator-facing tracker for the human-dependent
evidence batches in the OR-CI next-stage plan. The tracker should identify
what can be sent, where returned files must be staged, which validator proves
receipt/readiness, and which blockers prevent the next report gate from
advancing.

## Requirements

- Add a generated tracker under the notes vault labeling operations experiment:
  - `human-evidence-collection-tracker-2026-05-27.csv`
  - `human-evidence-collection-tracker-2026-05-27.json`
  - `human-evidence-collection-tracker-2026-05-27.md`
- Add a builder script that reads existing readiness artifacts instead of
  duplicating hand-maintained state.
- Include at least these tracks:
  - cold protocol check;
  - 13-case capstone labeling;
  - Phase 2 50-case labeling;
  - NL4OPT external labeling;
  - mutation seed review.
- For each track, record:
  - current status;
  - actionable next operator action;
  - expected item count and completed item count;
  - sendable bundle or review package;
  - dispatch brief or operator queue;
  - return/staging target;
  - validation command;
  - blocker;
  - non-claim guardrail.
- The Markdown output must expose the primary next task and parallel ready
  tasks in a compact way suitable for the notes vault.
- The builder must support `--check` and fail when generated outputs are stale.
- Preserve all missing-evidence states:
  - do not create, infer, promote, or adjudicate labels;
  - do not mark capstone distribution unblocked;
  - do not mark any mutation seed accepted or run-eligible;
  - do not mark the paper evidence pack report-ready.

## Acceptance Criteria

- [x] Tracker CSV/JSON/Markdown are generated and committed in the notes vault.
- [x] `--check` detects stale tracker outputs.
- [x] Tracker records cold check as the primary next action with 0/5 complete.
- [x] Tracker records Phase 2 and NL4OPT bundles as send-ready but label-pending.
- [x] Tracker records capstone as blocked behind cold protocol readiness.
- [x] Tracker records mutation seed review as pending human seed reviews with
      0 accepted seeds and 0 run-eligible mutation rows.
- [x] Existing labeling handoff, distribution, leakage, promotion, board, and
      paper-readiness checks still pass.
- [ ] Notes changes and Trellis archive are committed.

## Out Of Scope

- Do not collect or synthesize human labels.
- Do not change rater packets, distribution ZIP contents, baseline responses,
  mutation seed decisions, cost fields, or paper branch decisions.
