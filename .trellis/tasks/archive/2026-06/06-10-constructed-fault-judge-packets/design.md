# Design: Judge Packet Contract And Audit

## Boundary

Implementation lives in the OR-research experiment pack. OR-CI package code is
not modified. This task prepares packets for future LLM judge runs but does not
call any model provider.

## Data Flow

```text
materiality_ledger.csv
  -> filter denominator_bucket == material_valid
  -> build_judge_packets.py
  -> judge_packets/JP-*.json
  -> judge_packet_manifest.csv
  -> judge_packet_contract.md
  -> judge_packet_audit.{md,json}
  -> updated run plan / claim notes
```

## Packet Shape

Each judge-visible packet contains:

- `packet_id`: anonymous ID like `JP-001-<hash>`.
- `schema_version`: `constructed_source_fidelity_judge_packet_v1`.
- `case`: non-leaking case metadata such as seed case ID.
- `source_statement`: original natural-language statement text.
- `candidate_artifact`: candidate ProblemSpec JSON and submission source.
- `or_ci_evidence`: status, classification, checks, failures, and model summary.
- `judge_variants`: three prompt configurations and expected response schema.
- `instructions`: decide whether the candidate artifact is source faithful.

The packet intentionally does not include mutation ID, fault family,
materiality class, oracle status, objective deltas, or mutation metadata.

## Manifest Shape

`judge_packet_manifest.csv` is internal and maps:

- packet ID;
- seed case ID;
- mutation ID;
- fault family;
- packet path;
- source statement path;
- candidate ProblemSpec path;
- candidate submission path;
- OR-CI report path;
- audit status.

The manifest is not input to LLM judges.

## Leakage Audit

The audit checks every packet filename and JSON payload for forbidden content:

- exact mutation IDs;
- fault-family strings;
- mutation metadata strings and paths;
- materiality/oracle fields;
- source-fidelity oracle/layered replay decisions;
- objective delta fields;
- hidden ground-truth labels.

Seed case IDs are allowed because source statements and artifacts already use
BWOR case identity. Packet IDs must not encode mutation/fault semantics.

## Result Recording

This task records contract readiness, not judge detection outcomes. It updates
the experiment pack to say LLM judge execution is now unblocked, while model
calls remain deferred to the next task.

## Rollback

Regeneration is idempotent. `build_judge_packets.py` rewrites only
`judge_packets/`, `judge_packet_*` artifacts, and the relevant experiment
planning/audit notes.
