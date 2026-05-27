# Baseline direct P001-P002 captures

## Goal

Verify or rerun the first direct_strong_llm Extended Pro baseline responses, then stage and promote only valid JSON with exact frozen model metadata.

## Confirmed Facts

- The next-stage roadmap keeps human cold-check labels as the critical path,
  while baseline response capture remains an implementable parallel
  evidence-collection track.
- The baseline operator queue currently has 52 rows, 39 captured/recorded
  rows, 13 remaining submissions, and 0 issues.
- Completed baseline captures cover P001-P013 for `llm_judge_no_rubric`,
  `llm_judge_rubric`, and `llm_judge_evidence_checklist`.
- The only remaining baseline-response condition is `direct_strong_llm`,
  currently 0/13.
- Historical Oracle attempt text exists for P001 and P002, but it may be used
  only if session metadata proves the frozen Extended Pro policy. Otherwise it
  remains failed or non-accepted infrastructure evidence.
- Captured direct responses are bookkeeping evidence only. They must not be
  used to claim baseline performance, FAR reduction, source-fidelity accuracy,
  or paper branch readiness before all baseline rows and adjudicated human
  labels exist.

## Requirements

- Target only:
  - `baseline_condition=direct_strong_llm`
  - `packet_id=P001`
  - `packet_id=P002`
- Check existing direct P001/P002 attempt artifacts and Oracle session metadata
  before submitting new model runs.
- Accept historical attempt output only if it:
  - parses as exactly one JSON object;
  - matches `baseline_condition=direct_strong_llm`;
  - matches the targeted packet id;
  - can be augmented with the frozen staged metadata;
  - has Oracle browser session evidence for `resolvedLabel=Extended Pro` and
    extended thinking time;
  - passes `build_baseline_response_intake.py --check`.
- If historical evidence is missing or policy-noncompliant, rerun the targeted
  row with Oracle browser mode against ChatGPT Extended Pro using:
  - `--model gpt-5.5-pro`
  - `--browser-model-strategy select`
  - `--browser-thinking-time extended`
  - the shared remote Chrome session when available.
- Save Oracle's final assistant answer under
  `baseline-ablation-oracle-attempts-2026-05-27/`.
- Save only valid JSON objects to the staged response-intake paths:
  - `baseline-ablation-response-intake-2026-05-27/direct_strong_llm/P001.json`
  - `baseline-ablation-response-intake-2026-05-27/direct_strong_llm/P002.json`
- Promote each valid staged row explicitly through
  `build_baseline_response_intake.py --promote --baseline-condition
  direct_strong_llm --packet-id <packet>`.
- After promotion, rerun baseline intake, capture, ablation results, operator
  queue, paper-readiness, and next-stage board checks.
- Keep roadmap/review-sync/current-source notes consistent with the resulting
  baseline count.
- Do not stage or promote Instant, ordinary Pro, invalid JSON, failed attempt
  transcripts, or any response whose model metadata differs from the frozen run
  queue.
- Do not infer or repair model output from failed attempts.

## Acceptance Criteria

- [x] Historical P001/P002 direct attempts are classified as accepted or
      rejected based on explicit Oracle session provenance.
- [x] Any accepted staged response JSON includes the exact frozen metadata:
      `model_or_tool=oracle-cli browser ChatGPT Extended Pro` and
      `model_version=gpt-5.5-pro thinking-heavy via Extended Pro`.
- [x] Valid P001/P002 staged JSON files, if available, pass intake validation
      and are promoted to canonical raw response files.
- [x] Baseline counts advance from 39/52 to 41/52 if both targeted rows are
      valid and promoted; otherwise only validated/promoted rows count.
- [x] Per-condition captured counts become `direct_strong_llm` 2/13 if both
      targeted rows are promoted, while each judge condition remains 13/13.
- [x] `build_baseline_response_intake.py --check`,
      `build_baseline_response_capture.py --check`,
      `build_baseline_ablation_results.py --check`, and
      `build_baseline_response_operator_queue.py --check` pass.
- [x] `build_paper_evidence_pack_readiness.py --check` and
      `build_next_stage_execution_board.py --check` pass while keeping
      `report_ready=false`.
- [x] `uv run pytest`, code and notes `git diff --check`, and GitNexus change
      detection pass before archive/commit.
- [x] No baseline performance, accuracy, false-accept, source-fidelity, or
      final paper-branch claim is created.

## Outcome

- Historical P001/P002 direct attempts with `resolvedLabel=Pro` were rejected
  for baseline promotion, even when their text was parseable.
- First fresh Extended Pro P001/P002 reruns had valid model provenance but
  invalid JSON wrappers, so they remain attempt evidence only.
- JSON-wrapper retries `direct-p001-extended-pro-json` and
  `direct-p002-extended-pro-json` had `resolvedLabel=Extended Pro`,
  `verified=true`, extended thinking, and valid JSON.
- P001/P002 were staged, promoted, and captured as canonical
  `direct_strong_llm` raw responses.
- Baseline response bookkeeping advanced to 41/52 captured responses; 11
  `direct_strong_llm` rows remain.
- Paper readiness remains `report_ready=false`.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
