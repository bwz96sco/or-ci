# Guarded returned evidence staging

## Goal

Add a dry-run-first staging helper for returned human label and seed-review
CSVs so external files can be validated and copied into the correct intake
targets without manual overwrites or premature evidence claims.

## Confirmed Facts

- The current primary blocker is external human evidence collection.
- Returned cold-check, capstone, Phase 2, NL4OPT, and mutation seed-review
  CSVs are staged in fixed intake paths before downstream validators run.
- The existing intake validators already classify pending, partial, complete,
  and invalid rows after files are staged.
- Current staging targets are blank templates or missing files; no returned
  evidence is present.

## Requirements

- Add a notes-side script under
  `experiments/or-ci-labeling-operations-2026-05-26/`.
- Default behavior must preview a proposed staging operation and change no
  files.
- `--execute` is required before copying a source CSV into an intake target.
- The helper must support these targets:
  - `cold_protocol_check`;
  - `capstone_rater_a`;
  - `capstone_rater_b`;
  - `phase2_50case_rater_a`;
  - `phase2_50case_rater_b`;
  - `nl4opt_rater_a`;
  - `nl4opt_rater_b`;
  - `mutation_seed_review`.
- It must validate source CSV presence, header compatibility, expected row
  count, target path, and optional source SHA-256.
- It must refuse to overwrite a target that already contains any completed or
  partial returned data unless an explicit future overwrite mode is added.
- It must refuse placeholder source paths and must not accept generated
  readiness CSVs as returned evidence.
- It must print the exact follow-up intake/check command for the target.
- Add `--check` mode for the staging target registry.
- Add `--self-test` mode that validates the copy path in temporary files and
  rejects missing source, wrong header, SHA mismatch, nonblank target, and
  placeholder source.
- Wire `--check` and `--self-test` into the evidence-gate smoke report.
- Preserve all no-label/no-send/no-claim constraints in the current run.

## Acceptance Criteria

- [x] `stage_returned_human_evidence.py` exists.
- [x] `--check` passes and lists all supported staging targets.
- [x] `--self-test` passes.
- [x] A dry-run with a placeholder/missing source is rejected.
- [x] Current intake targets remain unchanged; no returned labels or seed
      reviews are staged.
- [x] Evidence-gate smoke includes the staging helper check/self-test and
      passes with `report_ready=false`.
- [x] Existing intake, receipt, paper-readiness, execution-board, and smoke
      checks still pass.
- [x] The task creates no protocol-review decision, send event, returned
      evidence, labels, mutation outcome, accepted seed, adjudication decision,
      or report-ready claim.

## Notes

- This helper is for after an external rater/reviewer returns a file. It must
  not synthesize returned evidence.
