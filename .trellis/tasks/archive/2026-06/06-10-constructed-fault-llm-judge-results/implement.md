# Implementation Plan

## Checklist

1. Add Oracle log summary constants to `constructed_fault_common.py`.
2. Update `run_llm_judge_pilot.py` to:
   - summarize completed-response state correctly;
   - generate Oracle log summary artifacts;
   - upsert LLM judge result rows;
   - upsert C4 claim;
   - update analysis/writing/audit/claim notes.
3. Regenerate LLM judge artifacts.
4. Run validation commands.
5. Commit OR-research artifacts.
6. Commit/archive Trellis metadata.

## Validation Commands

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python /Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10/run_llm_judge_pilot.py
PYTHONDONTWRITEBYTECODE=1 uv run python /Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10/run_llm_judge_pilot.py --check
PYTHONDONTWRITEBYTECODE=1 uv run python /Users/zhangbowen/Projects/agent-skills-private/skills/research-experiment/scripts/validate_experiment_pack.py /Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10 --strict-claim-audit
uv run pytest
```

Before OR-CI commits:

```bash
npx gitnexus detect-changes --repo or-ci --scope staged
```
