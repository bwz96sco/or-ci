# Implementation checklist

- [x] Add `build_human_time_evidence_readiness.py` and generated event/readiness
      artifacts in the labeling-operations experiment directory.
- [x] Wire `build_cost_evidence_operator_packet.py` to read the new readiness
      source for human label/adjudication minutes.
- [x] Wire `build_paper_evidence_pack_readiness.py` to require and validate the
      new readiness source.
- [x] Add the readiness check and self-test to `build_evidence_gate_smoke_report.py`.
- [x] Regenerate dependent artifacts: human-time readiness, cost operator
      packet, paper readiness, draft, execution board, and smoke report.
- [x] Run focused checks and self-tests, then full notes smoke.
- [x] Run `uv run pytest` in the code repo and `npx gitnexus detect-changes`
      before committing Trellis/code-repo metadata.

## Validation commands

Run from `/Users/zhangbowen/Projects/OR/note/OR-research`:

- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-labeling-operations-2026-05-26/build_human_time_evidence_readiness.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-labeling-operations-2026-05-26/build_human_time_evidence_readiness.py --self-test`
- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-paper-evidence-pack-2026-05-27/build_cost_evidence_operator_packet.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-paper-evidence-pack-2026-05-27/build_paper_evidence_pack_readiness.py --check`
- `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-paper-evidence-pack-2026-05-27/build_evidence_gate_smoke_report.py --check`

Run from `/Users/zhangbowen/Projects/OR/code/or-ci`:

- `uv run pytest`
- `npx gitnexus detect-changes --repo or-ci --scope all`
