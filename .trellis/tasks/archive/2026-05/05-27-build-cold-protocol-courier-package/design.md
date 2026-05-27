# Design: Cold Protocol Courier Package

## Context

The execution board correctly marks the cold protocol bundle as `safe_to_send`,
but the coordinator currently has to open several artifacts to gather the ZIP,
message, receipt recorder command, and return-staging commands. A courier
package reduces dispatch friction while preserving the rule that local
automation must not fabricate external evidence.

## Approach

Add `build_cold_protocol_courier_package.py` in the notes-vault labeling
operations folder. The builder reads the existing
`cold-protocol-send-packet-2026-05-27.json` as the source of truth and copies
the already-generated rater ZIP into a courier directory. It then writes a
README, rater message, manifest JSON, checksum CSV, and summary JSON/Markdown.

The check mode rebuilds expected file contents in memory, verifies the copied
ZIP digest, and compares all generated artifacts. The self-test asserts the
current pre-send state: ready to send, pending external dispatch, no
sent/returned metadata, report still non-ready, and no generated courier
artifact claiming dispatch occurred.

## Non-Goals

- Do not send the package.
- Do not record receipt events.
- Do not stage returned CSVs or time logs.
- Do not alter label intake, promotion, adjudication, cost, or paper readiness.
