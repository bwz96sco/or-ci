# Session Record: OR-CI Agent-Mode Integration Pilot

Date: 2026-05-17

## Decisions

- The practical integration pilot path is `or_llm_agent` agent mode plus
  standalone OR-CI verification.
- `api` mode remains useful as a provider baseline, but it is still blocked in
  the current environment by provider authentication.
- `agent` mode is the preferred local pilot path when Codex CLI authentication
  works because it does not depend on OpenAI-compatible provider keys.
- Parent-run OR-CI verification remains the source of truth for pilot
  classification, even when nested Codex runs OR-CI during its own repair loop.

## Actions Taken

- Reran the integration pilot with:

```bash
uv run or-llm-agent pilot \
  --mode agent \
  --ids BWOR-001 BWOR-002 BWOR-010 \
  --artifact-dir ../or-ci/artifacts/pilot/phase-1-integration-agent-2026-05-16-rerun \
  --codex-timeout-seconds 900
```

- Fixed `or_llm_agent` agent-mode execution after observing that nested
  `codex exec` can no-op with `input_tokens=0` when `-C` points inside the
  OR-CI repository or artifact tree.
- Changed nested Codex execution to use a neutral cache work directory and pass
  the requested OR-CI artifact directory with `--add-dir`.
- Added parent-side fallback artifact harvesting from the neutral Codex work
  directory into the requested OR-CI pilot artifact directory.
- Added focused regression tests in `or_llm_agent/tests/test_codex_agent.py`
  for command construction, prompt fallback instructions, and artifact harvest.
- Updated `or_llm_agent` plan/spec docs to document the neutral-workdir and
  fallback-harvest contract.
- Recorded the implementation and pilot outcome to mempal as
  `drawer_experiments_paper_planning_70ea23d8`.

## Pilot Result

- Final report:
  `artifacts/pilot/phase-1-integration-agent-2026-05-16-rerun/report.md`
- `BWOR-001`: generation `generated`, OR-CI classification `SUCCESS`
- `BWOR-002`: generation `generated`, OR-CI classification `SUCCESS`
- `BWOR-010`: generation `generated`, OR-CI classification `SUCCESS`
- All three reports passed:
  - `original_solver_status`
  - `cost_scaling`
  - `constraint_relaxation`

## Next Work

- Commit the `or_llm_agent` agent-mode robustness fix, tests, and docs.
- Decide whether to keep the pilot artifact directory under version control or
  summarize it in notes only.
- Scale the pilot beyond the three-problem micro-batch and track generation
  failures, semantic failures, repair attempts, runtime, and artifact
  completeness.
- Revisit API-mode baseline runs only after provider authentication is fixed.

## Notes

- `SUCCESS` means the generated submission passed the configured OR-CI
  invariants. It is not a proof of full mathematical correctness.
- The current successful pilot validates the workflow and artifact contract, not
  the paper-scale experimental claim.
