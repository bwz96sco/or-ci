# Baseline P004 Judge Captures

## Goal

Capture and promote the three P004 judge-style Extended Pro baseline
responses, if and only if Oracle returns valid JSON that passes the existing
response-intake gate.

This task intentionally excludes `direct_strong_llm/P004`; direct-LLM rows are
kept separate because earlier direct rows have policy/retry history and need a
separate decision path.

## Target Rows

- `llm_judge_no_rubric/P004`
- `llm_judge_rubric/P004`
- `llm_judge_evidence_checklist/P004`

## Requirements

- Use the existing manual bundles:
  - `baseline-ablation-manual-submissions-2026-05-27/llm_judge_no_rubric/P004.md`
  - `baseline-ablation-manual-submissions-2026-05-27/llm_judge_rubric/P004.md`
  - `baseline-ablation-manual-submissions-2026-05-27/llm_judge_evidence_checklist/P004.md`
- Submit each row with Oracle CLI browser mode using:
  - `--model gpt-5.5-pro`
  - `--browser-model-strategy select`
  - `--browser-thinking-time extended`
  - the shared remote Chrome session when available.
- Save each Oracle final assistant answer under
  `baseline-ablation-oracle-attempts-2026-05-27/`.
- Accept only responses that:
  - parse as exactly one JSON object;
  - match the requested `baseline_condition` and `packet_id=P004`;
  - include all required baseline decision fields;
  - can be augmented with the frozen staged metadata;
  - pass `build_baseline_response_intake.py --check`.
- For each valid row, stage the JSON at the expected intake path and promote
  exactly that row with the existing `build_baseline_response_intake.py
  --promote` command.
- For each invalid or policy-noncompliant row, do not stage or promote it;
  write failure evidence only.
- Do not retry for answer quality.

## Acceptance Criteria

- [x] Oracle attempt outputs are recorded for all three target rows.
- [x] Each valid/policy-compliant row is promoted to its canonical raw-response
      file and has a completed response-template row.
- [x] Each invalid/policy-noncompliant row has no staged or canonical response
      and has failure evidence. No target row was invalid or policy-noncompliant.
- [x] Baseline intake, capture, ablation results, operator queue,
      paper-readiness, and execution board checks pass.
- [x] No baseline performance, accuracy, false-accept, source-fidelity, or final
      paper-branch claim is created.

## Out Of Scope

- Do not submit or promote `direct_strong_llm/P004` in this task.
- Do not submit packet ids other than `P004`.
- Do not infer, repair, or edit model decisions beyond adding required staged
  metadata.
