# Baseline Judge P001 Extended Pro Capture

## Goal

Capture one validated Extended Pro baseline response for
`llm_judge_no_rubric/P001`, then promote it through the existing response-intake
gate if and only if it is valid JSON and policy-compliant.

## Requirements

- Target only:
  - `baseline_condition=llm_judge_no_rubric`
  - `packet_id=P001`
  - `case_id=BWOR-001`
- Use the existing manual bundle:
  `baseline-ablation-manual-submissions-2026-05-27/llm_judge_no_rubric/P001.md`.
- Submit with Oracle CLI browser mode using:
  - `--model gpt-5.5-pro`
  - `--browser-model-strategy select`
  - `--browser-thinking-time extended`
  - the shared remote Chrome session when available.
- Save Oracle's final assistant answer under
  `baseline-ablation-oracle-attempts-2026-05-27/`.
- Accept only a response that:
  - parses as exactly one JSON object;
  - matches `baseline_condition=llm_judge_no_rubric`;
  - matches `packet_id=P001`;
  - includes all required baseline decision fields;
  - can be augmented with the frozen staged metadata;
  - passes `build_baseline_response_intake.py --check`.
- If valid, stage the JSON at
  `baseline-ablation-response-intake-2026-05-27/llm_judge_no_rubric/P001.json`.
- If staged valid, promote exactly this row with
  `build_baseline_response_intake.py --promote --baseline-condition llm_judge_no_rubric --packet-id P001`.
- After promotion, rerun capture, results, operator queue, paper-readiness, and
  next-stage board checks.
- If invalid or policy-noncompliant, do not stage or promote; write a failure
  note only.

## Acceptance Criteria

- [x] Oracle attempt output is recorded under the attempt evidence directory.
- [x] If valid and policy-compliant, a canonical raw response exists at
      `baseline-ablation-raw-responses-2026-05-26/llm_judge_no_rubric/P001.json`
      and the response template row is completed.
- [x] If invalid or policy-noncompliant, no staged or canonical response is
      created and a failure note explains the rejection.
      Not applicable: the response was valid and was promoted.
- [x] Baseline intake, capture, ablation results, operator queue,
      paper-readiness, and execution board checks pass.
- [x] No baseline performance, accuracy, false-accept, source-fidelity, or final
      paper-branch claim is created.

Outcome: Oracle session `or-ci-baseline-judge-no` returned valid JSON with
`resolved=Extended Pro`; the staged response passed intake and was promoted to
canonical raw-response bookkeeping. The baseline response count moved from
0/52 to 1/52.

## Out Of Scope

- Do not submit direct-generation rows in this task.
- Do not submit other judge conditions or packet ids in this task.
- Do not infer or repair model output from failed attempt text.
- Do not treat a captured baseline response as paper-grade evidence until it is
  paired with adjudicated human labels.
