# Baseline direct P003-P004 captures

## Goal

Capture, stage, promote, and validate the next `direct_strong_llm` Extended Pro baseline responses for P003 and P004.

## Confirmed Facts

- The next-stage roadmap keeps human cold-check labels as the critical path,
  while baseline response capture remains an implementable parallel
  evidence-collection track.
- The baseline operator queue currently has 52 rows, 41 captured/recorded
  rows, 11 remaining submissions, and 0 issues.
- Completed baseline captures cover P001-P013 for `llm_judge_no_rubric`,
  `llm_judge_rubric`, and `llm_judge_evidence_checklist`, plus P001-P002 for
  `direct_strong_llm`.
- The only remaining baseline-response condition is `direct_strong_llm`,
  currently 2/13.
- Captured direct responses are bookkeeping evidence only. They must not be
  used to claim baseline performance, FAR reduction, source-fidelity accuracy,
  or paper branch readiness before all baseline rows and adjudicated human
  labels exist.

## Requirements

- Target only:
  - `baseline_condition=direct_strong_llm`
  - `packet_id=P003`
  - `packet_id=P004`
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
  - `baseline-ablation-response-intake-2026-05-27/direct_strong_llm/P003.json`
  - `baseline-ablation-response-intake-2026-05-27/direct_strong_llm/P004.json`
- If the first answer has valid Extended Pro provenance but invalid JSON
  wrapping, use the frozen-policy retry allowance once for JSON-wrapper repair.
  Do not retry for answer quality.
- Promote each valid staged row explicitly through
  `build_baseline_response_intake.py --promote --baseline-condition
  direct_strong_llm --packet-id <packet>`.
- After promotion, rerun baseline intake, capture, ablation results, baseline
  comparison, operator queue, paper-readiness, and next-stage board checks.
- Keep roadmap/review-sync/current-source notes consistent with the resulting
  baseline count.
- Do not stage or promote Instant, ordinary Pro, invalid JSON, failed attempt
  transcripts, or any response whose model metadata differs from the frozen run
  queue.
- Do not infer or repair model output from failed attempts.

## Acceptance Criteria

- [x] Oracle attempt outputs are recorded for P003 and P004.
- [x] Any accepted staged response JSON includes the exact frozen metadata:
      `model_or_tool=oracle-cli browser ChatGPT Extended Pro` and
      `model_version=gpt-5.5-pro thinking-heavy via Extended Pro`.
- [x] Valid P003/P004 staged JSON files pass intake validation and are promoted
      to canonical raw response files.
- [x] Baseline counts advance from 41/52 to 43/52 if both targeted rows are
      valid and promoted; otherwise only validated/promoted rows count.
- [x] Per-condition captured counts become `direct_strong_llm` 4/13 if both
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

- P003 and P004 were submitted through Oracle browser ChatGPT Extended Pro with
  extended thinking and no browser attachments.
- P003 returned valid JSON on the first accepted Extended Pro attempt.
- P004's first Extended Pro attempt was retained as provenance but rejected for
  invalid JSON wrapping; the one allowed JSON-wrapper retry returned valid JSON.
- Both accepted rows were staged in the response-intake directory and promoted
  into canonical raw responses with the frozen metadata.
- Generated readiness outputs now record 43/52 captured baseline responses,
  `direct_strong_llm` at 4/13, and 9 remaining baseline rows, all in the
  `direct_strong_llm` condition.
- Paper evidence readiness remains `report_ready=false`; no baseline
  performance, FAR, accuracy, or paper-branch claim was introduced.

## Verification

- `build_baseline_response_intake.py --check`: 52 expected, 0 promotable.
- `build_baseline_response_capture.py --check`: 52 expected, 43 present.
- `build_baseline_ablation_results.py --check`: 43 completed, 9 pending.
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
