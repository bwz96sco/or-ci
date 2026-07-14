# Build returned-artifact staging runbook

## Goal

Add a generated notes-vault operator runbook that maps each expected returned
external artifact to the correct dry-run staging command, execute command,
validation command, and non-claim guardrail. This should reduce coordinator
error after human returns arrive without recording send events, returned events,
labels, time, seed reviews, or report-ready claims.

## Requirements

- Generate `returned-artifact-staging-runbook-2026-05-27.{json,csv,md}` from
  current dispatch/outbox/staging sources.
- Include rows for:
  - cold protocol returned label sheet;
  - cold protocol returned time log;
  - Phase 2 Rater A and Rater B returned sheets;
  - Phase 2 returned time log;
  - NL4OPT Rater A and Rater B returned sheets;
  - NL4OPT returned time log;
  - mutation seed review returned CSV.
- Include blocked capstone return rows as non-actionable context, since the
  capstone package must not be sent until the cold protocol review decision is
  accepted.
- Commands must default to dry-run and show the explicit `--execute` form
  separately.
- Returned source paths must be placeholders of the form
  `<returned ...>` so generated examples never point at blank in-bundle
  templates as evidence.
- The runbook must preserve current evidence semantics:
  - do not create or mutate returned labels;
  - do not append human-time events;
  - do not record dispatch receipt events;
  - keep paper readiness and report output blocked.
- Wire the runbook check into the evidence-gate smoke report.

## Acceptance Criteria

- [x] The runbook generator has `--check` and `--self-test` modes.
- [x] Generated JSON/CSV/Markdown contain actionable rows for safe-to-send /
      safe-to-review waves and blocked rows for capstone context.
- [x] Every staging command uses dry-run by default and every execute command
      is explicit.
- [x] No generated command uses a real bundle path as the returned source; all
      returned sources are `<returned ...>` placeholders.
- [x] Full evidence-gate smoke passes after regeneration.
- [x] Human-time event CSV remains header-only and paper `report_ready` remains
      false.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-labeling-operations-2026-05-26/build_returned_artifact_staging_runbook.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-labeling-operations-2026-05-26/build_returned_artifact_staging_runbook.py --self-test`
- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-paper-evidence-pack-2026-05-27/build_evidence_gate_smoke_report.py --check`
- `jq '{command_count: (.commands|length), status, report_ready}' experiments/packs/or-ci-paper-evidence-pack-2026-05-27/evidence-gate-smoke-report-2026-05-27.json` -> 84 commands, `all_smoke_gates_passed`, `report_ready=false`
- `wc -l experiments/packs/or-ci-labeling-operations-2026-05-26/human-time-evidence-events-2026-05-27.csv` -> 1 header line
- `uv run pytest` -> 42 passed
- `npx gitnexus detect-changes --repo or-ci --scope all` -> `No changes detected.`
