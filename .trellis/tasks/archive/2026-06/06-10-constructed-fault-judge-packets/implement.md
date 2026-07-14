# Implementation Plan

## Checklist

1. Add judge-packet output constants to `constructed_fault_common.py`.
2. Implement `build_judge_packets.py`.
3. Generate:
   - `judge_packet_contract.md`
   - `judge_packets/JP-*.json`
   - `judge_packet_manifest.csv`
   - `judge_packet_audit.md`
   - `judge_packet_audit.json`
4. Update `03_run_plan.md` and `run_matrix.yaml` to mark packet contract
   readiness.
5. Update Stage 06/07 notes conservatively:
   - `results_ledger.csv`
   - `claim_ledger.csv`
   - `claim_update.md`
   - optionally `analysis_campaign.md` / `writing_handoff.md` if useful.
6. Add `--check` validation for packet count, stale files, forbidden leakage,
   anonymous IDs, and manifest separation.
7. Run quality checks.
8. Commit OR-research artifacts, then commit/archive Trellis metadata.

## Validation Commands

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python /Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10/build_judge_packets.py
PYTHONDONTWRITEBYTECODE=1 uv run python /Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10/build_judge_packets.py --check
PYTHONDONTWRITEBYTECODE=1 uv run python /Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10/run_acceptance_layer_replay.py --check
PYTHONDONTWRITEBYTECODE=1 uv run python -m py_compile /Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10/constructed_fault_common.py /Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10/build_judge_packets.py
PYTHONDONTWRITEBYTECODE=1 uv run python /Users/zhangbowen/Projects/agent-skills-private/skills/research-experiment/scripts/validate_experiment_pack.py /Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10 --strict-claim-audit
uv run pytest
```

Before OR-CI commits:

```bash
npx gitnexus detect-changes --repo or-ci --scope staged
```

## Risk Points

- Packet IDs and filenames must not leak mutation/fault-family labels.
- Packet JSON must not include materiality labels, source-fidelity oracle
  decisions, or objective deltas.
- Manifest can contain internal mapping, but it must not be used as judge input.
- This task must not call LLMs or spend provider budget.
- Leave unrelated `.mcp.json` unstaged.

## Completion Definition

The task is complete when packet generation and audit pass, the experiment pack
states that LLM judge execution is unblocked but deferred, strict validation and
OR-CI tests pass, and all intended artifacts are committed.
