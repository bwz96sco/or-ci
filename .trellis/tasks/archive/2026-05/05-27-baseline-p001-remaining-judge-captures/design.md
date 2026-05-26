# Design

## Boundary

This task owns two baseline response rows:

- `llm_judge_rubric/P001`
- `llm_judge_evidence_checklist/P001`

It may write Oracle attempt outputs, staged response JSON files, canonical raw
responses through the existing promotion command, regenerated readiness
artifacts, and failure notes if needed. It must not manually edit canonical raw
responses outside the promotion command and must not create paper claims.

## Acceptance Path Per Row

1. Oracle saves the final assistant answer to the attempt evidence directory.
2. Inspect the session log/metadata for Pro/Extended Pro evidence and
   `thinkingTime=extended`.
3. Parse the saved answer as JSON.
4. Add staged metadata:
   - `run_id`
   - `model_or_tool=oracle-cli browser ChatGPT Extended Pro`
   - `model_version=gpt-5.5-pro thinking-heavy via Extended Pro`
5. Write staged JSON at the expected row path.
6. Run the response-intake check.
7. Promote exactly the row with the existing `--promote` command.
8. Regenerate/check downstream artifacts.

## Failure Path Per Row

If model evidence, JSON parsing, staged validation, or promotion fails, preserve
the attempt output and write a row-specific failure note. No staged or
canonical response should remain unless it has passed the validator.

## Non-Claim Guard

Captured baseline responses are bookkeeping only until paired with adjudicated
human labels. No paper metric, false-accept, or source-fidelity claim is allowed
from these captures alone.
