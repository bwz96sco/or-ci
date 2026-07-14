# Implementation Plan

## Checklist

1. Add acceptance-layer output path constants to `constructed_fault_common.py`.
2. Implement `run_acceptance_layer_replay.py` in the experiment pack.
3. Generate:
   - `acceptance_layer_replay_ledger.{csv,json,md}`
   - `acceptance_layer_summary.{csv,json,md}`
   - `acceptance_layer_execution_log.md`
4. Update standard research-experiment Stage 05/06 outputs to include the new
   acceptance-layer claim without losing the materiality claim:
   - `execution_log.md`
   - `results_ledger.csv`
   - `result_audit.md`
   - `claim_ledger.csv`
   - `claim_update.md`
5. Update `03_run_plan.md` with Milestone 4 completion notes.
6. Add `--check` validation for denominator, layer coverage, summary
   consistency, and denominator exclusions.
7. Run quality checks.
8. Commit OR-research artifacts, then archive and commit Trellis task metadata.

## Validation Commands

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python /Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10/run_acceptance_layer_replay.py
PYTHONDONTWRITEBYTECODE=1 uv run python /Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10/run_acceptance_layer_replay.py --check
PYTHONDONTWRITEBYTECODE=1 uv run python -m py_compile /Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10/constructed_fault_common.py /Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10/run_acceptance_layer_replay.py
PYTHONDONTWRITEBYTECODE=1 uv run python /Users/zhangbowen/Projects/agent-skills-private/skills/research-experiment/scripts/validate_experiment_pack.py /Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10 --strict-claim-audit
uv run pytest
```

Before OR-CI commits:

```bash
npx gitnexus detect-changes --repo or-ci --scope staged
```

## Risk Points

- Do not count invalid or silent/equivalent mutants in the material
  false-accept denominator.
- Do not treat OR-CI `SUCCESS` as source fidelity.
- Avoid using mutation metadata for execution, answer-only, or OR-CI decisions.
- Preserve validator-compatible Stage 05/06 files.
- Leave unrelated `.mcp.json` changes unstaged.

## Completion Definition

The task is complete when the deterministic acceptance replay table proves
which layers accept or reject each of the 10 material-valid mutants, strict
research-experiment validation passes, OR-CI tests pass, and all intended
artifacts are committed.
