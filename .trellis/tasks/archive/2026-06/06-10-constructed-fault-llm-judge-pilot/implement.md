# Implementation Plan

## Checklist

1. Add LLM judge output constants to `constructed_fault_common.py`.
2. Implement `run_llm_judge_pilot.py`.
3. Generate:
   - `llm_judge_request_queue.jsonl`
   - `llm_judge_prompts/*.md`
   - `llm_judge_response_schema.json`
   - `llm_judge_response_template.json`
   - `llm_judge_execution_plan.md`
   - `llm_judge_results.csv`
   - `llm_judge_summary.{csv,json,md}`
   - `llm_judge_execution_log.md`
4. Update analysis/writing handoff and run matrix to record queued state.
5. Add `--check` validation for queue count, prompt freshness, prompt leakage,
   schema freshness, and result/summary consistency.
6. Run quality checks.
7. Commit OR-research artifacts, then commit/archive Trellis metadata.

## Validation Commands

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python /Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10/run_llm_judge_pilot.py
PYTHONDONTWRITEBYTECODE=1 uv run python /Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10/run_llm_judge_pilot.py --check
PYTHONDONTWRITEBYTECODE=1 uv run python /Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10/build_judge_packets.py --check
PYTHONDONTWRITEBYTECODE=1 uv run python /Users/zhangbowen/Projects/agent-skills-private/skills/research-experiment/scripts/validate_experiment_pack.py /Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10 --strict-claim-audit
uv run pytest
```

Before OR-CI commits:

```bash
npx gitnexus detect-changes --repo or-ci --scope staged
```

## Risk Points

- Prompt generation must not read hidden manifest content.
- Queue readiness must not be mistaken for LLM judge evidence.
- Missing response files must be visible as missing external evidence.
- Any future provider execution must preserve request IDs and raw response paths.
- Leave unrelated `.mcp.json` unstaged.

## Completion Definition

The task is complete when the runner produces a 30-request prompt queue, the
queued/no-response state is validated, the experiment pack records the external
response barrier clearly, strict validation and OR-CI tests pass, and intended
artifacts are committed.
