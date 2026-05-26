# Next-Stage Execution Control Board Design

## Boundary

The implementation lives in the notes vault, not the OR-CI verifier package:

`/Users/zhangbowen/Projects/OR/note/OR-research/experiments/or-ci-paper-evidence-pack-2026-05-27/`

It reads existing generated summaries and writes a derived board. It must not
edit source labels, staged responses, seed-review decisions, mutation rows, or
report-ready flags.

## Inputs

Authoritative inputs are existing generated JSON files:

- `paper-evidence-pack-readiness-2026-05-27.json`
- `human-labeling-gate-summary-2026-05-27.json`
- `baseline-response-operator-queue-2026-05-27.json`
- `mutation-seed-review-operator-queue-2026-05-27.json`
- `label-promotion-readiness-2026-05-27.json`

The generator fails if any source is missing. It does not silently substitute
older files.

## Outputs

The generator writes:

- `next-stage-execution-board-2026-05-27.csv`
- `next-stage-execution-board-2026-05-27.json`
- `next-stage-execution-board-2026-05-27.md`

CSV is the operator table. JSON stores summary counts and source references.
Markdown is the human-facing control board.

## Row Contract

Each row has:

- `priority`
- `track`
- `action_id`
- `current_status`
- `next_action`
- `owner_type`
- `required_count`
- `completed_count`
- `blocked_by`
- `proof_artifact`
- `verification_command`
- `forbidden_claim`

Rows are deterministic and sorted by `priority`.

## Status Rules

The board status is `pending_external_evidence_collection` while any required
external evidence remains missing. The primary next action is the cold protocol
check until its intake gate records completed debug labels.

This board is deliberately not wired into
`build_paper_evidence_pack_readiness.py` to avoid a generated-artifact cycle:
readiness can feed the board, but the board should not feed readiness.

## Non-Claims

The board repeats forbidden claims from the paper-readiness artifact and adds
track-specific non-claims. It may say a gate is ready for distribution or
pending, but it must not say evidence exists until the corresponding source
gate says so.
