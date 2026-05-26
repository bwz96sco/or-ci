# Source fidelity rubric and capstone report

## Goal

Add a structured source-fidelity rubric and capstone report output to OR-LLM-Agent while preserving OR-CI as the deterministic verifier.

The user needs report-ready evidence that separates "OR-CI verified the generated spec/code pair" from "the generated spec is faithful to the original source statement." The resulting batch report must expose rejected, provisional, unsupported, and incomplete-data cases instead of letting raw OR-CI pass counts become the headline claim.

## Confirmed Facts

- Implementation belongs in the sibling `../or_llm_agent` producer repo, not in the OR-CI verifier.
- OR-CI remains deterministic and does not import LLM/provider/review logic.
- Existing OR-LLM-Agent fidelity flow already has `review-fidelity`, `review-fidelity-batch`, `resolve-fidelity`, and `resolve-fidelity-batch`.
- Existing fidelity output is flat: `accepted` / `rejected`, confidence, issues, review note, and evidence.
- Existing batch reports track `spec_fidelity_status` and `spec_fidelity_gate_status`, but do not aggregate dimension-level source-fidelity evidence.
- Known weak spots to make visible include incomplete data, unsupported stochastic scope, multi-scenario objective undercheck, routing/TSP cost-scaling-only coverage, MIQP/pairwise unit ambiguity, and provisional clarification assumptions.

## Requirements

- Add a versioned `source_fidelity_v1` rubric to fidelity reviews.
- Require agent-mode fidelity reviews to return dimension-level evidence.
- Keep manual/legacy review payloads readable, but mark flat reviews as legacy and exclude them from rubric-complete aggregate metrics.
- Store dimension results in each case's `spec/fidelity-review.json` and show them in `spec/fidelity-review.md`.
- Add summary fields for failed dimensions, blocking dimension count, warning dimension count, provisional status, and materiality.
- Enforce hard-block rejection when accepted reviews contain major or critical failures in source-critical dimensions.
- Distinguish source/human-backed clarification from provisional agent assumptions.
- Add preflight risk flags for known source-fidelity weak spots.
- Add batch-level `fidelity-rubric-summary.json` and `fidelity-rubric-report.md`.
- Extend the existing batch markdown report to reference the rubric summary when available.

## Acceptance Criteria

- [ ] A manual flat review still works and is marked as legacy-flat.
- [ ] An agent review without the required rubric dimensions is rejected as rubric-incomplete.
- [ ] An accepted review with a hard-block dimension failure is rejected.
- [ ] A complete accepted rubric review writes dimension details, summary counters, and markdown table output.
- [ ] A provisional clarification dependency is visible in summary JSON, case markdown, and batch capstone output.
- [ ] Batch review writes aggregate rubric JSON and markdown outputs.
- [ ] Batch capstone includes goal, claim boundary, aggregate counts, case matrix, boundary taxonomy, and capstone conclusion.
- [ ] Existing failed-verification acceptance guard remains intact.
- [ ] `uv run pytest tests/test_problemspec_generation.py` passes in `../or_llm_agent`.
- [ ] `uv run pytest tests` passes in `../or_llm_agent`.

## Notes

- Archived plan is saved in `plan.md`.
- Automated tests should mock reviewer payloads; they must not require live nested Codex, Oracle, or network calls.
