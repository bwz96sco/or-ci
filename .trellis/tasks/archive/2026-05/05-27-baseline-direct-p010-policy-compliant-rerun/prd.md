# Baseline direct P010 policy-compliant rerun

## Goal

Add an auditable infrastructure-failure retry addendum for the remaining direct_strong_llm P010 baseline row, then capture/promote a valid Extended Pro JSON response if available.

## Confirmed Facts

- The next-stage execution board reports baseline responses at 51/52.
- The only remaining baseline-response row is `direct_strong_llm` / `P010`.
- `P010` has two historical failed attempts:
  - first attempt: valid JSON, but Oracle browser metadata resolved ordinary
    Pro rather than Extended Pro;
  - retry attempt: ordinary Pro plus ChatGPT page-error text, not valid JSON.
- The current frozen policy allows max retries of `1` and rejects Instant,
  ordinary Pro, page-error text, invalid JSON, and all non-Extended-Pro model
  metadata as completed baseline evidence.
- The current notes explicitly say another P010 attempt requires either valid
  Extended Pro JSON or an explicit frozen-policy update before retrying.
- Completing this row is bookkeeping evidence only. It does not permit baseline
  performance, FAR, accuracy, source-fidelity, or paper-branch claims before
  adjudicated human labels exist.

## Requirements

- Update the baseline model run policy with a narrow, auditable addendum for
  `direct_strong_llm` / `P010` only.
- The addendum must preserve the no-answer-quality-retry rule.
- The addendum may permit one additional attempt only because both prior P010
  attempts failed the declared model/runtime infrastructure contract before a
  valid Extended Pro JSON response existed.
- The addendum must state that ordinary Pro JSON and page-error text remain
  invalid and must not be inferred into a baseline result.
- Submit P010 through Oracle browser mode with:
  - `--model gpt-5.5-pro`
  - `--browser-model-strategy select`
  - `--browser-thinking-time extended`
  - `--browser-attachments never`
  - `--browser-archive never`
  - shared remote Chrome when available.
- Accept the new attempt only if Oracle session evidence proves Extended Pro
  and the final answer is a valid single JSON object matching the baseline
  schema.
- Stage only accepted JSON at
  `baseline-ablation-response-intake-2026-05-27/direct_strong_llm/P010.json`.
- Promote the staged row explicitly with
  `build_baseline_response_intake.py --promote --baseline-condition
  direct_strong_llm --packet-id P010`.
- Regenerate/check baseline intake, capture, ablation results, operator queue,
  baseline comparison, paper-readiness, and next-stage board artifacts.
- Keep all roadmap/reconciliation/sync notes aligned with the resulting count.
- If the new attempt still fails model metadata or JSON validation, record it
  only as failure evidence, leave P010 pending, and do not stage or infer it.

## Acceptance Criteria

- [x] `baseline-model-run-policy-2026-05-27.md` contains the P010
      infrastructure-failure retry addendum.
- [x] A new Oracle attempt output for P010 is saved under
      `baseline-ablation-oracle-attempts-2026-05-27/`.
- [x] If accepted, P010 staged JSON records exact frozen metadata:
      `model_or_tool=oracle-cli browser ChatGPT Extended Pro` and
      `model_version=gpt-5.5-pro thinking-heavy via Extended Pro`.
- [x] If accepted, P010 is promoted to canonical raw response/template
      artifacts and baseline counts advance to 52/52 with
      `direct_strong_llm` at 13/13.
- [x] Rejected-attempt branch is not used; no invalid attempt was staged or
      inferred.
- [x] All baseline/readiness check commands pass after the attempt is handled.
- [x] `uv run pytest`, code and notes `git diff --check`, task validation, and
      GitNexus change detection pass before archive/commit.
- [x] No baseline performance, accuracy, false-accept, source-fidelity, or
      final paper-branch claim is created.

## Outcome

- Added a P010-only infrastructure-failure retry addendum to the baseline model
  run policy. The addendum preserves the no-answer-quality-retry rule and keeps
  ordinary Pro, page-error text, non-Extended-Pro metadata, and invalid JSON as
  invalid evidence.
- Ran Oracle session `direct-p010-extended-pro-json-3` with browser mode,
  `gpt-5.5-pro`, model picker strategy `select`, extended thinking, no
  attachments, and no archive. Oracle session evidence records
  `resolved=Extended Pro` and `verified=yes`.
- Saved the new attempt output at
  `baseline-ablation-oracle-attempts-2026-05-27/direct_strong_llm-P010-extended-pro-json-rerun-output.txt`.
- Staged P010 at
  `baseline-ablation-response-intake-2026-05-27/direct_strong_llm/P010.json`
  with the exact frozen metadata, then promoted it to canonical raw response
  artifacts.
- Regenerated baseline/readiness artifacts. Baseline response capture is now
  52/52, `direct_strong_llm` is 13/13, and paper readiness remains
  `report_ready=false` / `pending_required_evidence`.
- Updated roadmap, review-sync, and review-reconciliation notes so the next
  baseline action is human-label pairing, not more model submission.

## Verification

- `build_baseline_response_intake.py --check`: 52 expected, 0 promotable.
- `build_baseline_response_capture.py --check`: 52 expected, 52 present.
- `build_baseline_ablation_results.py --check`: 52 completed, 0 pending.
- `build_baseline_response_operator_queue.py --check`: 52 rows,
  `status=baseline_response_capture_complete_pending_results_and_labels`.
- `build_baseline_comparison.py --check`: passed for 13 artifacts.
- `build_paper_evidence_pack_readiness.py --check`: 15 sections,
  `status=pending_required_evidence`.
- `build_next_stage_execution_board.py --check`: 8 rows,
  `status=pending_external_evidence_collection`.
- `uv run pytest`: 42 passed.
- Code and notes `git diff --check`: passed.
- `task.py validate`: passed.
- `npx gitnexus detect-changes --repo or-ci --scope all`: no changes detected.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
