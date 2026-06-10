# Finalize LLM judge result evidence

## Goal

Finalize the constructed-fault LLM judge pilot after external Oracle/ChatGPT
browser responses have been collected. Convert the 30 response files into
validated result evidence, record provider/log provenance, and update the
research ledgers and claims without overclaiming model-picker certainty.

## Requirements

- Work in the OR-research experiment pack:
  `/Users/zhangbowen/Projects/OR/note/OR-research/experiments/constructed-source-fidelity-fault-benchmark-2026-06-10/`.
- Keep OR-CI verifier/package code unchanged.
- Preserve all 30 response JSON files under `llm_judge_responses/`.
- Preserve invalid first-attempt responses under `llm_judge_invalid_responses/`.
- Preserve Oracle/browser run logs under `llm_judge_oracle_logs/`.
- Update `run_llm_judge_pilot.py` so completed-response state is not described
  as queued-only.
- Add Oracle log summary artifacts:
  - `llm_judge_oracle_log_summary.csv`
  - `llm_judge_oracle_log_summary.json`
  - `llm_judge_oracle_log_summary.md`
- Update result and claim ledgers with an LLM judge result claim:
  - no-rubric false accepts 3/10;
  - source-fidelity-rubric false accepts 2/10;
  - evidence-checklist false accepts 3/10;
  - all 30 response files validate against the schema.
- Record model-selection caveat: Oracle browser route reports
  `gpt-5.5-pro[browser]`, but ChatGPT picker verification was not available in
  logs (`verified=no` / resolved unavailable), so the result must not claim a
  verified UI model-picker state.
- Update `analysis_campaign.md`, `writing_handoff.md`, `result_audit.md`, and
  `claim_update.md` with actual LLM judge outcomes.
- Use `uv` for Python commands.

## Acceptance Criteria

- [ ] Trellis planning artifacts are complete and validated.
- [ ] `run_llm_judge_pilot.py --check` passes with status
      `llm_judge_results_ready`.
- [ ] `llm_judge_summary.json` shows 30 valid responses, 0 missing, 0 invalid.
- [ ] Oracle log summary artifacts exist and capture available session/model
      evidence.
- [ ] Claim/result ledgers include LLM judge result rows/claims.
- [ ] Research-experiment pack validation passes with
      `--strict-claim-audit`.
- [ ] `uv run pytest` passes in OR-CI.
- [ ] GitNexus staged-scope checks run before OR-CI Trellis commits.

## Notes

- This task records the pilot result, not a natural-distribution rate or human
  rater agreement result.
