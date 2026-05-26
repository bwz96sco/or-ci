# Baseline P002 Extended Pro capture attempt

## Goal

Attempt one fresh baseline response capture for
`direct_strong_llm/P002` using Oracle CLI browser mode and the frozen
ChatGPT Extended Pro policy.

## Requirements

- Use the existing manual bundle
  `baseline-ablation-manual-submissions-2026-05-27/direct_strong_llm/P002.md`.
- Submit through Oracle CLI browser mode with model `gpt-5.5-pro`.
- Store Oracle's final assistant output as attempt evidence.
- Accept a response only if:
  - the answer is valid JSON;
  - it matches `baseline_condition=direct_strong_llm`;
  - it matches `packet_id=P002`;
  - it includes required staged metadata;
  - it records exactly the frozen Extended Pro model/tool metadata required by
    the response-intake validator.
- If the answer is invalid JSON or not Extended Pro, do not stage it as a
  baseline response. Record it only as failed attempt evidence.
- Keep failed attempt output separate from canonical raw responses.
- Regenerate/check baseline response gates after the attempt.

## Acceptance Criteria

- [x] Oracle attempt output is recorded in the attempt evidence directory.
- [x] If invalid or policy-noncompliant, no staged/canonical response is
      created and the failure note explains why.
- [x] Baseline response intake, capture, and operator queue checks pass.
- [x] No baseline performance, accuracy, or false-accept claim is created.

The valid/policy-compliant promotion path did not apply: Oracle resolved the
run as ordinary `Pro`, not `Extended Pro`, and the saved answer was invalid
JSON.

## Notes

- P001 direct strong-LLM already exhausted the frozen retry budget and must not
  be rerun in this task.
