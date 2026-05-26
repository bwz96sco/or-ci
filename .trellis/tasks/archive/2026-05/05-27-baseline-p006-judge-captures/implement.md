# Baseline P006 Judge Captures Implementation Plan

## Checklist

- [x] Confirm no existing P006 staged/raw/attempt files for targeted rows.
- [x] Start the Trellis task.
- [x] Load project specs with `trellis-before-dev`.
- [x] Run Oracle sequentially for the three P006 judge manual bundles.
- [x] Parse each output, add frozen metadata, and stage valid JSON.
- [x] Validate and promote each targeted row.
- [x] Regenerate baseline and paper-readiness derived artifacts.
- [x] Update current plan notes if baseline counts change.
- [x] Run validation commands.
- [x] Archive the task and commit notes/task evidence.

## Execution Notes

- `llm_judge_no_rubric/P006` first resolved to plain `Pro`, so that output was
  kept only as attempt evidence. The retry `p006-judge-no-extended` resolved
  to `Extended Pro` and was promoted.
- `llm_judge_rubric/P006` first resolved to plain `Pro`, so that output was
  kept only as attempt evidence. The retry `p006-judge-rubric-extended`
  resolved to `Extended Pro` and was promoted.
- `llm_judge_evidence_checklist/P006` resolved to `Extended Pro` on the first
  explicit-label run and was promoted.
- Promoted decisions:
  - `llm_judge_no_rubric/P006`: `blocked`
  - `llm_judge_rubric/P006`: `rejected`
  - `llm_judge_evidence_checklist/P006`: `rejected`
- Regenerated summaries now report 18 completed baseline rows and 34 pending
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
