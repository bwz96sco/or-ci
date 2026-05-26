# Design

## Boundary

The task owns exactly one baseline row: `llm_judge_no_rubric/P001`. It may
write attempt evidence, one staged response JSON, and canonical raw response
bookkeeping through the existing promotion command. It must not manually edit
canonical raw responses or paper claims.

## Acceptance Path

1. Oracle saves the final assistant answer to the attempt evidence directory.
2. Inspect the session log/metadata for Pro model selection and extended
   thinking-time control.
3. Parse the saved answer as JSON.
4. Add staged metadata:
   - `run_id`
   - `model_or_tool=oracle-cli browser ChatGPT Extended Pro`
   - `model_version=gpt-5.5-pro thinking-heavy via Extended Pro`
5. Write staged JSON at the row's expected intake path.
6. Run the response-intake check.
7. Promote exactly this row with the existing `--promote` command.
8. Run capture/results/operator/paper/board validators.

## Failure Path

If model evidence, JSON parsing, staged validation, or promotion fails, preserve
the attempt output and write a failure note. No staged or canonical response
should remain unless it has passed the relevant validator.

## Data Contract

The model answer must match `baseline-ablation-output-schema-2026-05-26.md`
plus staged metadata. The response-intake script is the authoritative validator;
manual inspection cannot override it.

## Non-Claim Guard

Promotion is bookkeeping for baseline response capture only. It does not create
baseline accuracy, false-accept, source-fidelity, or final report claims.
