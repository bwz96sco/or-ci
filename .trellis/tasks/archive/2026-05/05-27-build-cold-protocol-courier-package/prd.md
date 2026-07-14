# Build cold protocol courier package

## Goal

Create a generated coordinator courier package for the immediate 5-case cold
protocol check. The package should put the sendable ZIP, copy-ready message,
checksum manifest, and after-send/after-return command references in one folder
so the coordinator can dispatch the bundle without assembling scattered
artifacts.

## Requirements

- Generate `cold-protocol-courier-package-2026-05-27/` under the labeling
  operations experiment.
- Include a copy of the existing cold-protocol rater ZIP, not a rebuilt or
  modified rater bundle.
- Include:
  - `COURIER-README.md` with the exact current send/return workflow;
  - `rater-message.txt` with subject and message body;
  - `courier-manifest.json` with source paths, checksums, current receipt
    state, and non-claims;
  - `courier-checksums.csv` covering all courier payload files.
- Generate companion `cold-protocol-courier-package-2026-05-27.{json,md}`
  summaries.
- Provide `--check` and `--self-test` modes.
- Wire the courier package check and self-test into the evidence-gate smoke
  report.
- The package must not record a send, stage returned files, write receipt
  events, create labels, promote labels, or change paper readiness.

## Acceptance Criteria

- [x] Courier folder exists and contains the rater ZIP copy plus README,
  message, manifest, and checksum CSV.
- [x] Courier manifest reports `send_allowed=true`,
  `receipt_status=pending_external_dispatch`, and `status=ready_to_send` in the
  current state.
- [x] SHA-256 of the copied ZIP matches the source send-packet ZIP SHA.
- [x] Generated commands are preview/check instructions only unless explicitly
  labeled as post-send/post-return operator commands.
- [x] `--check` and `--self-test` pass.
- [x] Evidence-gate smoke passes and command count increases by 2.
- [x] Paper `report_ready` remains false.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-labeling-operations-2026-05-26/build_cold_protocol_courier_package.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-labeling-operations-2026-05-26/build_cold_protocol_courier_package.py --self-test`
- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-paper-evidence-pack-2026-05-27/build_evidence_gate_smoke_report.py --check`
- Paper readiness remains `report_ready=false`.
