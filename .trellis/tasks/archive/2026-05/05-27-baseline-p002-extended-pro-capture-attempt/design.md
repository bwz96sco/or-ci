# Baseline P002 Extended Pro Capture Attempt Design

## Boundary

The attempt targets one row only:

- `baseline_condition=direct_strong_llm`
- `packet_id=P002`

The task may write attempt evidence under
`baseline-ablation-oracle-attempts-2026-05-27/`. It may write a staged response
only if the response is valid JSON and passes the frozen metadata policy. It
must not write canonical raw responses directly.

## Acceptance Path

1. Oracle writes final assistant output to an attempt text file.
2. Parse the text as JSON.
3. Add or require staged metadata fields:
   - `run_id`
   - `model_or_tool=oracle-cli browser ChatGPT Extended Pro`
   - `model_version=gpt-5.5-pro thinking-heavy via Extended Pro`
4. Run `build_baseline_response_intake.py --check`.

If any step fails, the output remains attempt evidence only.

## Failure Path

Invalid JSON, ordinary Pro/Instant model evidence, missing required fields, or
Oracle/browser errors are recorded in an attempt note. The operator queue remains
pending for this row.
