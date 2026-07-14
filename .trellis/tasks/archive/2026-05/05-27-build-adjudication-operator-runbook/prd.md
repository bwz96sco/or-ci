# Build adjudication operator runbook

## Goal

Add a generated notes-vault runbook that tells the coordinator what
post-intake agreement/adjudication artifact to run for each labeled dataset,
what evidence is still blocking it, and which claims remain forbidden. The
runbook must stay blocked in the current state because no human labels have
been promoted yet.

## Requirements

- Generate `adjudication-operator-runbook-2026-05-27.{json,csv,md}` from
  current promotion, intake, agreement, and paper-readiness artifacts.
- Include rows for:
  - 13-case capstone;
  - Phase 2 50-case pilot;
  - NL4OPT external sanity check.
- For each dataset, include:
  - intake status and promotion status;
  - canonical rater input files;
  - adjudication sheet/worktable files;
  - agreement/adjudication check command;
  - blocker text;
  - claim guardrail.
- The runbook must not copy labels, fill adjudication sheets, promote labels, or
  compute final claims.
- Wire the runbook check into the evidence-gate smoke report.

## Acceptance Criteria

- [x] The runbook generator has `--check` and `--self-test` modes.
- [x] Generated JSON/CSV/Markdown contain three dataset rows.
- [x] Current rows are blocked until label intake and promotion are complete.
- [x] Commands are check-only; no generated command includes `--execute`.
- [x] Full evidence-gate smoke passes after regeneration.
- [x] Paper `report_ready` remains false.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-labeling-operations-2026-05-26/build_adjudication_operator_runbook.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-labeling-operations-2026-05-26/build_adjudication_operator_runbook.py --self-test`
- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-paper-evidence-pack-2026-05-27/build_evidence_gate_smoke_report.py --check`
- `uv run pytest`
- Paper readiness remains `report_ready=false`.
