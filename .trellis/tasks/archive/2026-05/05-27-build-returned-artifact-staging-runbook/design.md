# Design: Returned-artifact staging runbook

## Context

The project now has separate guarded helpers for returned labels/seed reviews
and returned human-time logs. The next operator risk is using the wrong helper,
staging to the wrong target, or accidentally treating a blank bundle-local file
as returned evidence.

## Approach

Add `build_returned_artifact_staging_runbook.py` in the labeling operations
folder. It reads current generated sources rather than hand-maintaining the
runbook:

- `human-dispatch-outbox-preflight-2026-05-27.json`
- `cold-protocol-send-packet-2026-05-27.json`
- `parallel-human-dispatch-send-packets-2026-05-27.json`
- capstone distribution/intake sources for blocked context

The script writes:

- `returned-artifact-staging-runbook-2026-05-27.json`
- `returned-artifact-staging-runbook-2026-05-27.csv`
- `returned-artifact-staging-runbook-2026-05-27.md`

Rows include artifact kind, track/wave, preflight status, returned source
placeholder, staging target, dry-run command, execute command, validation
command, and guardrails.

## Non-Goals

- Do not stage or copy any returned file.
- Do not record send or return receipt events.
- Do not append human-time evidence rows.
- Do not unblock capstone, labels, mutation execution, cost evidence, or report
  output.
