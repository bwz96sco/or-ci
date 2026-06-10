# Build LLM judge pilot runner

## Goal

Implement the next constructed-fault benchmark work package: prepare a
deterministic LLM judge pilot runner over the frozen judge packets, with a
provider-agnostic request queue, response-schema validation, and result
summaries that can be filled after external model responses are collected.

The user value is to make the LLM judge pilot executable and auditable without
mixing hidden mutation labels into prompts or relying on ad hoc manual response
parsing.

## Requirements

- Work in the OR-research experiment pack:
  `/Users/zhangbowen/Projects/OR/note/OR-research/experiments/constructed-source-fidelity-fault-benchmark-2026-06-10/`.
- Add a deterministic script, `run_llm_judge_pilot.py`.
- The script must read only the frozen judge-visible packet files under
  `judge_packets/` for prompt construction. It may read
  `judge_packet_manifest.csv` only for internal scoring after response files
  exist.
- Generate one request per packet and judge variant:
  - 10 packets x 3 variants = 30 request rows.
  - Variants: `no_rubric`, `source_fidelity_rubric`, `evidence_checklist`.
- Generate support artifacts:
  - `llm_judge_request_queue.jsonl`
  - `llm_judge_prompts/*.md`
  - `llm_judge_response_schema.json`
  - `llm_judge_response_template.json`
  - `llm_judge_execution_plan.md`
  - `llm_judge_results.csv`
  - `llm_judge_summary.{csv,json,md}`
  - `llm_judge_execution_log.md`
- Response ingestion must be file-based:
  - model/provider responses are placed under `llm_judge_responses/`;
  - the script validates JSON shape and controlled enum values;
  - invalid/missing responses are recorded without blocking request-queue
    readiness.
- The script must compute summary counts when valid responses are present:
  accepted, rejected, indeterminate, false-accept count, detection count, and
  parse/validation status by variant.
- Until actual external model responses exist, summary status must clearly say
  `ready_for_external_model_responses`, not claim LLM judge detection results.
- No model provider call is made by default. Any Oracle/browser/API execution is
  a separate explicit external step.
- Do not expose mutation IDs, fault-family labels, materiality labels, objective
  deltas, or source-fidelity oracle labels in prompt files.
- Update `analysis_campaign.md`, `writing_handoff.md`, `run_matrix.yaml`, and
  claim/result notes enough to record that the LLM judge pilot is queued but
  external model responses are still missing.
- Use `uv` for Python commands.

## Acceptance Criteria

- [ ] Trellis planning artifacts are complete and validated.
- [ ] `run_llm_judge_pilot.py` generates a 30-row request queue and 30 prompt
      files from frozen judge packets.
- [ ] Prompt files do not contain hidden construction tokens or manifest paths.
- [ ] `run_llm_judge_pilot.py --check` passes in the queued/no-response state
      and verifies queue/prompt/schema freshness.
- [ ] If response files are present, invalid response JSON is reported in the
      result ledger rather than silently ignored.
- [ ] Existing judge packet check still passes.
- [ ] Research-experiment pack validation passes with
      `--strict-claim-audit`.
- [ ] `uv run pytest` passes in OR-CI.
- [ ] OR-CI package code remains unchanged.
- [ ] GitNexus staged-scope checks run before OR-CI Trellis commits.

## Notes

- This task removes the response-parsing and prompt-construction blocker. It
  does not claim that LLM judges have been run until external response files
  exist.
