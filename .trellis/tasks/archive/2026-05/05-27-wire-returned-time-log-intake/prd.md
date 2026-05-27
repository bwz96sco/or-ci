# Wire returned time-log intake

## Goal

Make returned rater `human-time-log.csv` files actionable by adding a guarded
operator helper that converts validated returned time-log rows into previewed
human-time evidence event rows. This closes the loop between the rater bundles
and `human-time-evidence-events-2026-05-27.csv` without fabricating any minutes
or recording events before the coordinator explicitly executes the operation.

## Requirements

- Add a dry-run-first helper for returned time logs:
  - validates the returned time-log CSV schema;
  - validates dataset, work kind, participant role, positive minutes, and
    start/end timestamps;
  - maps each returned row to the canonical human-time evidence event schema;
  - refuses duplicate event IDs or events already present in the operator event
    log;
  - writes only with `--execute`.
- Correct the cold-protocol time-log participant role to match the canonical
  human-time readiness role vocabulary.
- Update rater bundle/distribution/send surfaces as needed so the returned
  time-log helper is discoverable for the cold, capstone, Phase 2, and NL4OPT
  tracks.
- Preserve evidence semantics:
  - do not record any returned time event during generation/checks/self-tests;
  - keep `human-time-evidence-events-2026-05-27.csv` header-only in the current
    state;
  - keep paper readiness and final cost readiness blocked until real returned
    time logs are recorded.
- Wire the new helper into the evidence-gate smoke report.

## Acceptance Criteria

- [x] The helper has `--check` and `--self-test` modes and rejects malformed,
      blank, duplicate, non-positive, date-only, or placeholder time rows.
- [x] A valid dry-run prints the event rows it would append, follow-up commands,
      and a guardrail that no evidence is recorded without `--execute`.
- [x] Bundle time-log templates use canonical participant roles accepted by
      `build_human_time_evidence_readiness.py`.
- [x] Generated operator surfaces mention the helper as the next step after a
      returned time log arrives.
- [x] The operator event CSV remains header-only and readiness remains
      `pending_human_time_evidence` in the current generated state.
- [x] Full evidence-gate smoke passes after regeneration.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/or-ci-labeling-operations-2026-05-26/stage_returned_human_time_log.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/or-ci-labeling-operations-2026-05-26/stage_returned_human_time_log.py --self-test`
- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/or-ci-labeling-operations-2026-05-26/build_human_time_evidence_readiness.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/or-ci-paper-evidence-pack-2026-05-27/build_evidence_gate_smoke_report.py --check`
- `wc -l experiments/or-ci-labeling-operations-2026-05-26/human-time-evidence-events-2026-05-27.csv` -> `1`
- `uv run pytest` -> `42 passed`
- `npx gitnexus detect-changes --repo or-ci --scope all` -> `No changes detected.`

## Notes

- This task prepares evidence ingestion only. It must not simulate or invent
  human work.
