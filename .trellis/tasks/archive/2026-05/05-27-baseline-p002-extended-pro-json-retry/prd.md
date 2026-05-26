# Baseline P002 Extended Pro Retry With Strict JSON

## Goal

Retry exactly one baseline response capture for `direct_strong_llm/P002` using
Oracle CLI browser mode, ChatGPT Pro with `extended` thinking time, and a
stricter JSON wrapper instruction. The retry should either produce one valid
staged Extended Pro response or a clearly recorded failed-attempt note.

## Requirements

- Target only the row:
  - `baseline_condition=direct_strong_llm`
  - `packet_id=P002`
- Use the existing manual bundle:
  `baseline-ablation-manual-submissions-2026-05-27/direct_strong_llm/P002.md`.
- Submit with Oracle CLI browser mode against the shared remote Chrome session
  when available.
- Use `--model gpt-5.5-pro`, `--browser-model-strategy select`, and
  `--browser-thinking-time extended`.
- Treat accepted model evidence as requiring:
  - the model picker resolves Pro; and
  - the Oracle log confirms `Thinking time: Extended` or equivalent selected /
    already-selected evidence.
- Store the raw assistant output in the attempt evidence directory first.
- Stage a response only if the saved answer is valid JSON and passes the
  baseline response-intake validator after adding required staged metadata.
- Required staged metadata:
  - `run_id`
  - `model_or_tool=oracle-cli browser ChatGPT Extended Pro`
  - `model_version=gpt-5.5-pro thinking-heavy via Extended Pro`
- If the answer is invalid JSON, ordinary/non-extended Pro, Instant, blocked by
  browser automation, or otherwise validator-noncompliant, do not stage or
  promote it; record failure evidence only.
- Do not rerun for answer quality. This task is the one allowed retry after the
  P002 invalid JSON / model-policy failure.

## Acceptance Criteria

- [x] The Oracle retry output is recorded under
      `baseline-ablation-oracle-attempts-2026-05-27/`.
- [x] If the retry is valid and policy-compliant, the staged JSON exists at
      `baseline-ablation-response-intake-2026-05-27/direct_strong_llm/P002.json`
      and `build_baseline_response_intake.py --check` reports it as promotable.
      Not applicable: the retry was invalid JSON and therefore was not staged.
- [x] If the retry is invalid or policy-noncompliant, no staged or canonical
      response is created and a failure note explains the rejection reason.
- [x] Baseline intake, capture, operator queue, paper-readiness, and execution
      board checks pass after the retry.
- [x] No baseline performance, accuracy, false-accept, source-fidelity, or final
      paper-branch claim is created.

Outcome: Oracle session `or-ci-baseline-p002-extended-2` completed, but the
saved output failed `json.loads` with `Expecting ',' delimiter at line 1 column
1242 char 1241` because `gurobi_python_code` again contained unescaped quotes.
No staged or canonical response was written.

## Out Of Scope

- Do not rerun `direct_strong_llm/P001`; its retry budget is exhausted under the
  current policy.
- Do not submit any other baseline row in this task.
- Do not fabricate, repair, or infer model answers from failed attempt text.
- Do not promote staged JSON to canonical raw responses unless explicitly
  executing the existing per-row promotion command after validation.
