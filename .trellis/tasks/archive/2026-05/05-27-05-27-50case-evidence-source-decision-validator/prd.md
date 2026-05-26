# Build 50-case evidence-source decision validator

## Goal

Add a validator and readiness report for the Phase 2 50-case evidence-source
coordinator decision gate without filling or changing coordinator decisions.

## Requirements

- Read the existing
  `source-fidelity-50case-evidence-source-decision-template-2026-05-26.csv`.
- Validate every row against the immutable artifact bridge and label manifest.
- Accept blank decision rows as pending, but validate any filled decision rows.
- Enforce allowed coordinator decisions:
  - `accept_existing`;
  - `copy_or_link_existing`;
  - `rerun_case`;
  - `exclude_pending_repair`.
- Require complete decision metadata for any filled row:
  - `coordinator_decision`;
  - `rerun_required`;
  - `decision_rationale`;
  - `reviewer_id`;
  - `decided_at`.
- Validate consistency between `coordinator_decision`, `rerun_required`, and
  `proposed_action`.
- Generate JSON and Markdown readiness reports.
- Include explicit non-claims that no evidence-source decision, human label,
  model response, or rerun result is created.
- Add `--check` validation for generated reports.

## Acceptance Criteria

- [x] Validator script runs with `uv run python`.
- [x] Current blank template validates as `pending_coordinator_decision`.
- [x] Readiness report records 50 total rows and 50 pending decisions.
- [x] Invalid partial decision metadata would fail validation.
- [x] Existing blank-template builder still passes `--check`.
- [x] Roadmap/integration/reconciliation notes reference the validator.
- [x] Notes repo is clean after commit.
- [x] Trellis task is archived after verification.

## Out of Scope

- Filling coordinator decision fields.
- Copying/linking artifacts.
- Rerunning OR-LLM-Agent.
- Distributing rater packets.
- Computing source-fidelity metrics.
