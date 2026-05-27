# Human dispatch outbox preflight

## Goal

Add a guarded notes-side outbox preflight for the human-evidence dispatch
waves. The preflight should prove the currently sendable bundles are fresh,
checksum-matched, not already recorded as sent, and paired with untouched
staging targets before a coordinator performs external dispatch.

## Requirements

- Add a builder under
  `experiments/or-ci-labeling-operations-2026-05-26/`.
- Generate deterministic JSON, CSV, and Markdown artifacts named
  `human-dispatch-outbox-preflight-2026-05-27.*`.
- Read the existing dispatch wave plan, receipt ledger, receipt events,
  leakage audit, cold/phase2/NL4OPT distribution summaries, cold intake
  readiness, and mutation seed-review queue.
- Produce one row for each dispatch wave:
  - cold protocol check;
  - cold protocol review;
  - capstone labels;
  - Phase 2 50-case labels;
  - NL4OPT external labels;
  - mutation seed review;
  - paper report output.
- For sendable package rows, verify:
  - package path exists;
  - file checksum and byte size match the wave metadata when metadata has a
    concrete ZIP SHA;
  - receipt status is still unsent or review-assignment pending;
  - rater-packet leakage audit has no high-severity issues;
  - intake or review target is still in a pending/blank state.
- For blocked rows, preserve the blocker and do not mark them sendable.
- The Markdown must surface the exact next operator action and receipt command
  template for rows that are safe to send or assign.
- Add `--check` to verify generated artifacts are fresh.
- Add `--self-test` to cover a ready package, a checksum mismatch, an already
  sent package, and a blocked package using temporary files.
- Wire the preflight into the paper evidence-gate smoke report.
- Preserve non-claim rules: do not send packages, record receipt events, create
  labels, promote labels, accept mutation seeds, adjudicate evidence, or change
  paper report readiness.

## Acceptance Criteria

- [x] `build_human_dispatch_outbox_preflight.py` exists.
- [x] `human-dispatch-outbox-preflight-2026-05-27.json`, `.csv`, and `.md`
      exist.
- [x] The generated preflight includes all 7 dispatch waves.
- [x] The cold protocol row is safe to send only while its bundle is present,
      checksum-matched, leakage-clean, unsent, and intake-pending.
- [x] Phase 2 and NL4OPT rows are safe to send only under the same guarded
      conditions.
- [x] Mutation seed review is assignable but not treated as a ZIP checksum
      row.
- [x] Cold protocol review, capstone, and paper report rows remain blocked in
      the current state.
- [x] `--check` passes.
- [x] `--self-test` passes.
- [x] Evidence-gate smoke includes the outbox preflight and still passes with
      `report_ready=false`.
- [x] No send event, returned evidence, human label, seed acceptance,
      adjudication, report-ready claim, or final paper branch decision is
      created.

## Notes

- This task advances operator readiness only. It is not a substitute for the
  external human send/return actions.
