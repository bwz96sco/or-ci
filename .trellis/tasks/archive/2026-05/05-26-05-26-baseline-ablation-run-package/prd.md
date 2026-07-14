# Build baseline ablation run package

## Goal

Create a deterministic baseline-ablation run queue and validation package that maps frozen prompt inputs to raw response paths and ledger policy without fabricating model responses.

## Confirmed Facts

- The notes experiment already freezes 52 baseline-ablation prompts:
  four conditions by thirteen packets.
- Existing validators check prompt inputs, the empty response template, and the
  downstream 13-case comparison scaffold.
- The runbook requires one frozen model/version per condition and raw response
  files recorded in the response template.
- Model responses and human labels are still pending; this task must not run a
  model silently or invent decisions.

## Requirements

- Add a baseline-ablation run package under
  `experiments/packs/or-ci-self-host-exploration-2026-05-25/`.
- Map every prompt-manifest row to a deterministic expected raw-response file
  path.
- Validate that every queued prompt file exists and that response paths are
  unique, condition-scoped, and under a dedicated raw-response directory.
- Derive run readiness from the current run ledger:
  - pending when model/tool or model version is not frozen;
  - ready only when condition-level model/version/temperature/retry policy is
    filled;
  - completed only when response template metadata and raw response JSON exist.
- Preserve the current state as `pending_model_runs`; no response JSON files or
  ablation decisions should be fabricated.
- Update the runbook and roadmap status so the next operator has a concrete
  checklist for running and ingesting the 52 external model responses.

## Acceptance Criteria

- [x] A run-package builder script exists and runs with `uv run python`.
- [x] The generated run queue contains exactly 52 condition-packet rows.
- [x] The generated summary reports zero completed rows and explains the model
      version/run-policy blocker.
- [x] `--check` validates prompt files, response paths, response template
      consistency, and run-ledger readiness.
- [x] Existing baseline input/result/comparison checks still pass.
- [x] `uv run pytest` for OR-CI still passes.
- [x] Roadmap status is updated without claiming baseline ablation completion.

## Out of Scope

- Running paid/external model calls.
- Choosing a model/version for the user.
- Filling response decisions without raw model output.
- Computing false-accept or accuracy metrics before human labels exist.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
