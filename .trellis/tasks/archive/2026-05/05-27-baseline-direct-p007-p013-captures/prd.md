# Baseline direct P007-P013 captures

## Goal

Capture, stage, promote, and validate the remaining `direct_strong_llm`
Extended Pro baseline responses for P007 through P013.

## Confirmed Facts

- The next-stage roadmap keeps human cold-check labels as the critical path,
  while baseline response capture remains an implementable parallel
  evidence-collection track.
- The baseline operator queue currently has 52 rows, 45 captured/recorded
  rows, 7 remaining submissions, and 0 issues.
- Completed baseline captures cover P001-P013 for `llm_judge_no_rubric`,
  `llm_judge_rubric`, and `llm_judge_evidence_checklist`, plus P001-P006 for
  `direct_strong_llm`.
- The only remaining baseline-response condition is `direct_strong_llm`,
  currently 6/13.
- Captured direct responses are bookkeeping evidence only. They must not be
  used to claim baseline performance, FAR reduction, source-fidelity accuracy,
  or paper branch readiness before all baseline rows and adjudicated human
  labels exist.

## Requirements

- Target only:
  - `baseline_condition=direct_strong_llm`
  - `packet_id=P007`
  - `packet_id=P008`
  - `packet_id=P009`
  - `packet_id=P010`
  - `packet_id=P011`
  - `packet_id=P012`
  - `packet_id=P013`
- Submit each targeted row with Oracle browser mode against ChatGPT Extended
  Pro using:
  - `--model gpt-5.5-pro`
  - `--browser-model-strategy select`
  - `--browser-thinking-time extended`
  - `--browser-attachments never`
  - the shared remote Chrome session when available.
- Use a freshly verified browser tab for each row and retain Oracle session
  evidence for `resolvedLabel=Extended Pro`, `verified=true`, and extended
  thinking time.
- Save Oracle's final assistant answer under
  `baseline-ablation-oracle-attempts-2026-05-27/`.
- Save only valid JSON objects to the staged response-intake paths:
  - `baseline-ablation-response-intake-2026-05-27/direct_strong_llm/P007.json`
  - `baseline-ablation-response-intake-2026-05-27/direct_strong_llm/P008.json`
  - `baseline-ablation-response-intake-2026-05-27/direct_strong_llm/P009.json`
  - `baseline-ablation-response-intake-2026-05-27/direct_strong_llm/P010.json`
  - `baseline-ablation-response-intake-2026-05-27/direct_strong_llm/P011.json`
  - `baseline-ablation-response-intake-2026-05-27/direct_strong_llm/P012.json`
  - `baseline-ablation-response-intake-2026-05-27/direct_strong_llm/P013.json`
- If the first answer has valid Extended Pro provenance but invalid JSON
  wrapping, use the frozen-policy retry allowance once for JSON-wrapper repair.
  Do not retry for answer quality.
- Promote each valid staged row explicitly through
  `build_baseline_response_intake.py --promote --baseline-condition
  direct_strong_llm --packet-id <packet>`.
- Promote rows sequentially or repair any response-template race before
  downstream capture validation. The final response template must remain a
  52-row CSV.
- After promotion, rerun baseline intake, capture, ablation results, baseline
  comparison, operator queue, paper-readiness, and next-stage board checks.
- Keep roadmap/review-sync/current-source notes consistent with the resulting
  baseline count.
- Do not stage or promote Instant, ordinary Pro, invalid JSON, failed attempt
  transcripts, or any response whose model metadata differs from the frozen run
  queue.
- Do not infer or repair model output from failed attempts.

## Acceptance Criteria

- [x] Oracle attempt outputs are recorded for P007-P013.
- [x] Any accepted staged response JSON includes the exact frozen metadata:
      `model_or_tool=oracle-cli browser ChatGPT Extended Pro` and
      `model_version=gpt-5.5-pro thinking-heavy via Extended Pro`.
- [x] Valid P007-P013 staged JSON files pass intake validation and are promoted
      to canonical raw response files.
- [x] Baseline counts advance from 45/52 to 52/52 if all targeted rows are
      valid and promoted; otherwise only validated/promoted rows count.
- [x] Per-condition captured counts become `direct_strong_llm` 13/13 if all
      targeted rows are promoted, while each judge condition remains 13/13.
- [x] `build_baseline_response_intake.py --check`,
      `build_baseline_response_capture.py --check`,
      `build_baseline_ablation_results.py --check`,
      `build_baseline_response_operator_queue.py --check`, and
      `build_baseline_comparison.py --check` pass.
- [x] `build_paper_evidence_pack_readiness.py --check` and
      `build_next_stage_execution_board.py --check` pass while keeping
      `report_ready=false`.
- [x] `uv run pytest`, code and notes `git diff --check`, and GitNexus change
      detection pass before archive/commit.
- [x] No baseline performance, accuracy, false-accept, source-fidelity, or
      final paper-branch claim is created.

## Outcome

- P007, P008, P009, P011, P012, and P013 were accepted for intake after
  verified Extended Pro sessions returned valid JSON.
- P009, P011, P012, and P013 each had one rejected first attempt before their
  accepted retry. Rejected attempts are retained only as provenance and are not
  staged.
- P010 remains pending. Its first attempt returned valid JSON but resolved to
  ordinary Pro; its one allowed retry also resolved to ordinary Pro and
  returned the ChatGPT page-error text. Neither P010 attempt was staged or
  inferred.
- Generated readiness outputs now record 51/52 captured baseline responses,
  `direct_strong_llm` at 12/13, and one remaining baseline row: P010.
- Paper evidence readiness remains `report_ready=false`; no baseline
  performance, FAR, accuracy, or paper-branch claim was introduced.
- The next baseline action is to resolve P010 with valid Extended Pro JSON or
  explicitly update the frozen retry policy before another attempt.

## Verification

- `build_baseline_response_intake.py --check`: 52 expected, 0 promotable.
- `build_baseline_response_capture.py --check`: 52 expected, 51 present.
- `build_baseline_ablation_results.py --check`: 51 completed, 1 pending.
- `build_baseline_response_operator_queue.py --check`: 52 rows,
  `status=pending_baseline_response_operator_actions`.
- `build_baseline_comparison.py --check`: passed for 13 artifacts.
- `build_paper_evidence_pack_readiness.py --check`: 15 sections,
  `status=pending_required_evidence`.
- `build_next_stage_execution_board.py --check`: 8 rows,
  `status=pending_external_evidence_collection`.
- `uv run pytest`: 42 passed.
- Code and notes `git diff --check`: passed.
- `npx gitnexus detect-changes --repo or-ci --scope all`: no changes
  detected.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
