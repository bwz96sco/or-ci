# Next-stage execution control board

## Goal

Create a deterministic next-stage execution control board for the OR-CI
research notes vault. The board should answer "what is the current situation
and what is next?" from the existing readiness gates without creating or
inferring any missing human labels, model responses, mutation results, or paper
claims.

## Requirements

- Add a notes-side Python generator under
  `experiments/or-ci-paper-evidence-pack-2026-05-27/`.
- Generate CSV, JSON, and Markdown artifacts for the 2026-05-27 next-stage
  execution board.
- Read existing readiness JSON/operator-queue artifacts as authoritative
  inputs:
  - paper evidence-pack readiness;
  - human-labeling gate summary;
  - baseline response operator queue;
  - mutation seed-review operator queue;
  - staged-label promotion readiness.
- Produce one concise action row per major track:
  - cold protocol check;
  - 13-case capstone labels;
  - 50-case labels;
  - NL4OPT labels;
  - Extended Pro baseline responses;
  - mutation seed reviews;
  - staged-label promotion;
  - report evidence pack.
- For each action row, include priority, current status, next action, owner
  type, required count, completed count, blocker, proof artifact, verification
  command, and forbidden claim.
- Make the Markdown artifact human-readable as a control board with:
  - current situation;
  - critical path;
  - parallel work;
  - verification commands;
  - forbidden claims.
- Add a `--check` mode that fails when any generated artifact is stale.
- Keep the output non-claiming: it may report scaffold readiness and missing
  evidence, but it must not report source-fidelity accuracy, FAR reduction,
  baseline performance, mutation recall, or external accuracy.
- Update the roadmap/reconciliation/sync notes to point to the generated board
  as the current execution surface.

## Acceptance Criteria

- [ ] `build_next_stage_execution_board.py` generates stable CSV, JSON, and
      Markdown artifacts.
- [ ] `uv run python build_next_stage_execution_board.py --check` passes after
      generation.
- [ ] The board reports `status=pending_external_evidence_collection` while
      human labels, Extended Pro responses, seed reviews, and final report
      evidence remain missing.
- [ ] The primary next action is the 5-case cold protocol check.
- [ ] The board preserves the parallel tracks for baseline response capture,
      mutation seed review, 50-case labels, and NL4OPT labels.
- [ ] The board does not mark the paper evidence pack report-ready and does
      not infer any empirical results.
- [ ] Related notes reference the generated board.
- [ ] Existing relevant validators still pass.

## Notes

- This is a coordination artifact, not an experiment result.
- The board is useful progress toward the long-term plan because it turns the
  review-synced roadmap into an executable operator surface.
