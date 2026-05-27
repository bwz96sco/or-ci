# Baseline P007 Judge Captures Implementation Plan

## Checklist

- [x] Confirm no existing P007 staged/raw/attempt files for targeted rows.
- [x] Start the Trellis task.
- [x] Load project specs with `trellis-before-dev`.
- [x] Run Oracle sequentially for the three P007 judge manual bundles.
- [x] Parse each output, add frozen metadata, and stage valid JSON.
- [x] Validate and promote each targeted row.
- [x] Regenerate baseline and paper-readiness derived artifacts.
- [x] Update current plan notes if baseline counts change.
- [x] Run validation commands.
- [x] Archive the task and commit notes/task evidence.

## Execution Notes

- `llm_judge_no_rubric/P007` resolved to `Extended Pro` and was promoted.
- `llm_judge_rubric/P007` first resolved to plain `Pro`, so that output was
  kept only as attempt evidence. The retry `p007-judge-rubric-extended`
  resolved to `Extended Pro` and was promoted.
- `llm_judge_evidence_checklist/P007` resolved to `Extended Pro` and was
  promoted.
- Promoted decisions:
  - `llm_judge_no_rubric/P007`: `accepted`
  - `llm_judge_rubric/P007`: `accepted`
  - `llm_judge_evidence_checklist/P007`: `accepted`
- Regenerated summaries now report 21 completed baseline rows and 31 pending
  rows. `direct_strong_llm` remains 0/13 and was not touched.

## Validation Commands

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python experiments/or-ci-self-host-exploration-2026-05-25/build_baseline_response_intake.py --check
PYTHONDONTWRITEBYTECODE=1 uv run python experiments/or-ci-self-host-exploration-2026-05-25/build_baseline_response_capture.py --check
PYTHONDONTWRITEBYTECODE=1 uv run python experiments/or-ci-self-host-exploration-2026-05-25/build_baseline_ablation_results.py --check
PYTHONDONTWRITEBYTECODE=1 uv run python experiments/or-ci-self-host-exploration-2026-05-25/build_baseline_response_operator_queue.py --check
PYTHONDONTWRITEBYTECODE=1 uv run python experiments/or-ci-paper-evidence-pack-2026-05-27/build_paper_evidence_pack_readiness.py --check
PYTHONDONTWRITEBYTECODE=1 uv run python experiments/or-ci-paper-evidence-pack-2026-05-27/build_next_stage_execution_board.py --check
uv run pytest
git diff --check
git -C /Users/zhangbowen/Projects/OR/note/OR-research diff --check
npx gitnexus detect-changes --repo or-ci --scope all
```
