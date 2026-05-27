# Gate paper readiness on distribution packages

## Goal

Update the paper evidence-pack readiness gate so human-labeling distribution
readiness is proven by deterministic distribution packages and coordinator
dispatch briefs, not only by source rater-bundle directories.

## Confirmed Facts

- The next-stage execution board now points Phase 2 and NL4OPT to sendable
  ZIPs, dispatch briefs, distribution summaries, and intake gates.
- The paper-readiness gate still snapshots primarily rater-bundle status for
  cold, capstone, Phase 2, and NL4OPT.
- The full research plan requires paper outputs to trace every table back to
  staged human labels, distribution packages, and guarded intake/promotion
  gates.
- This task must preserve missing-label states and `report_ready=false`.

## Requirements

- Add distribution-summary JSON inputs for cold protocol, capstone, Phase 2,
  and NL4OPT packages.
- Add coordinator dispatch briefs as required source files.
- Validate distribution summaries before considering a labeling package
  ready:
  - expected ready/blocking status;
  - ZIP path exists;
  - ZIP SHA-256 matches the summary;
  - completed label rows remain 0 for Phase 2/NL4OPT/cold/capstone where
    applicable;
  - report-ready remains false.
- Update paper-readiness rows, gate snapshots, and source artifacts to cite
  the distribution ZIPs/summaries/dispatch briefs alongside intake gates.
- Regenerate `paper-evidence-pack-readiness-2026-05-27.{csv,json,md}`.

## Acceptance Criteria

- [x] Paper-readiness gate checks cold/capstone/Phase 2/NL4OPT distribution
      summaries and ZIP hashes.
- [x] Generated Markdown gate snapshot lists distribution statuses and ZIP
      paths for cold/capstone/Phase 2/NL4OPT.
- [x] Label-related report rows cite distribution summary/dispatch/intake
      artifacts rather than only bundle-summary files.
- [x] `build_paper_evidence_pack_readiness.py --check` passes.
- [x] Existing board, handoff, distribution, leakage, and promotion checks pass.
- [x] Notes changes and Trellis archive are committed.

## Out Of Scope

- Do not create, infer, promote, or adjudicate human labels.
- Do not change baseline responses, mutation state, cost values, or final
  branch decision.
- Do not mark the paper evidence pack report-ready.
