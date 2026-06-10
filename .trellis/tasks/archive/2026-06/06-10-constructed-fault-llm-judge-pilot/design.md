# Design: LLM Judge Pilot Runner

## Boundary

Implementation lives in the OR-research experiment pack. OR-CI verifier package
code is not modified. The runner prepares prompts and parses response files; it
does not call a model provider by default.

## Data Flow

```text
judge_packets/JP-*.json
  -> run_llm_judge_pilot.py
  -> llm_judge_request_queue.jsonl
  -> llm_judge_prompts/*.md
  -> llm_judge_responses/*.json   # external, optional input
  -> llm_judge_results.csv
  -> llm_judge_summary.{csv,json,md}
```

Internal scoring may read `judge_packet_manifest.csv` only after responses are
present. Prompt construction must never read or embed the manifest.

## Request Shape

Each request row contains:

- `request_id`
- `packet_id`
- `judge_variant`
- `prompt_path`
- `packet_path`
- `response_path`
- `status`
- `hidden_inputs_used`

The queue contains 30 rows: 10 packets times 3 variants.

## Prompt Shape

Each prompt is Markdown with:

- source-fidelity judge role;
- exact variant instruction from the packet;
- required JSON response schema;
- full packet JSON fenced as judge-visible evidence;
- instruction to return JSON only.

Prompt files must not contain mutation IDs, fault-family labels, materiality
labels, objective deltas, source-fidelity oracle labels, or manifest paths.

## Response Ingestion

Responses are JSON files under `llm_judge_responses/`, one per request. The
runner validates:

- required keys;
- enum values;
- `reason_categories` controlled values;
- parse status.

Missing responses are `missing_response`. Invalid responses are
`invalid_response`. Valid responses are scored:

- accepted -> false accept on this constructed material denominator;
- rejected -> detected;
- indeterminate -> neither accepted nor detected.

## Result State

If no valid responses exist, summary status is
`ready_for_external_model_responses`. If at least one valid response exists,
summary status is `partial_llm_judge_results` until all 30 are valid. If all 30
are valid, status is `llm_judge_results_ready`.

## Safety

The runner checks prompt content against the same hidden-token set used by
`build_judge_packets.py`. It also fails if a prompt references
`judge_packet_manifest.csv` or raw planned-mutant paths.

## Rollback

Regeneration is idempotent. The runner rewrites only `llm_judge_*` artifacts and
updates research notes for queue readiness.
