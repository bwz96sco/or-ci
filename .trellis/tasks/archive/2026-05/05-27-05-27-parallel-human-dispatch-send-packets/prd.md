# Parallel human dispatch send packets

## Goal

Generate copy-ready send packets for the parallel-safe Phase 2, NL4OPT, and mutation seed-review waves, with package details and guarded receipt-event recorder commands, without recording sends or creating evidence.

## Confirmed Facts

- The active execution board has three parallel-safe human-evidence waves:
  `phase2_50case_labels`, `nl4opt_external_labels`, and
  `mutation_seed_review`.
- Phase 2 has a deterministic safe ZIP, distribution summary, dispatch brief,
  staged intake directory, and label-intake validator.
- NL4OPT has a deterministic safe ZIP, distribution summary, dispatch brief,
  staged intake directory, and label-intake validator.
- Mutation seed review has a reviewer-facing bundle directory, bundle summary,
  operator queue, staged intake target, and seed-review intake validator.
- The guarded receipt-event recorder already previews receipt rows by default
  and writes only with `--execute`.
- Current evidence state is still 0 Phase 2 labels, 0 NL4OPT labels, 0 seed
  reviews, and `report_ready=false`.

## Requirements

- Add a notes-side generator under
  `experiments/or-ci-labeling-operations-2026-05-26/`.
- Generate JSON and Markdown operator send-packet artifacts for the
  parallel-safe waves:
  - `phase2_50case_labels`;
  - `nl4opt_external_labels`;
  - `mutation_seed_review`.
- Read existing source artifacts rather than duplicating state:
  - human dispatch wave plan;
  - human dispatch receipt ledger;
  - receipt-events CSV;
  - Phase 2 distribution summary and dispatch brief;
  - NL4OPT distribution summary and dispatch brief;
  - mutation seed-review operator queue and bundle summary.
- Include package/bundle paths, checksums where available, archive roots,
  instructions, return files, expected returned staging targets, and validation
  commands.
- Include copy-ready outbound message text for each wave.
- Include guarded receipt-recorder dry-run and execute command templates for
  each wave.
- Validate that every included wave is currently ready to send or review,
  unsent in the receipt ledger/events, and points to existing package/bundle
  artifacts.
- Add `--check` mode that fails if generated artifacts are stale.
- Add `--self-test` mode that rejects unsafe states such as already-sent
  receipt rows, blocked waves, missing packages, or checksum mismatch.
- Wire check/self-test into the evidence-gate smoke report.
- Preserve all no-label/no-send/no-claim constraints.

## Acceptance Criteria

- [x] `parallel-human-dispatch-send-packets-2026-05-27.json` and
      `parallel-human-dispatch-send-packets-2026-05-27.md` are generated.
- [x] The generated packet includes Phase 2, NL4OPT, and mutation seed-review
      sections with copy-ready outbound text.
- [x] Every section includes package/bundle details and a guarded
      `record_human_dispatch_receipt_event.py` command template.
- [x] The current receipt-events CSV remains unchanged and no send is
      recorded.
- [x] `build_parallel_human_dispatch_send_packets.py --check` passes.
- [x] `build_parallel_human_dispatch_send_packets.py --self-test` passes.
- [x] `build_evidence_gate_smoke_report.py --check` includes the new checks
      and passes.
- [x] Existing receipt ledger, tracker, handoff, dashboard, paper readiness,
      and execution board checks still pass.
- [x] The task creates no send event, returned evidence, human labels, model
      responses, mutation outcomes, accepted seeds, adjudication decisions, or
      report-ready claims.

## Notes

- GitNexus impact for `command_specs` returned target-not-found / UNKNOWN.
  Practical blast radius is generated notes-vault operator packet and smoke
  artifacts, not indexed OR-CI verifier symbols.
