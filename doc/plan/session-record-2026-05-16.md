# Session Record: OR-CI Phase 1 Pilot Continuation

Date: 2026-05-16

## Decisions

- OR-CI means Operations Research Continuous Integration.
- ModelIR means Optimization Model Intermediate Representation.
- OR-CI is a standalone verifier package. `or_llm_agent` should consume it as a dependency or CLI tool, not own the OR-CI implementation.
- The first pilot process uses OR-CI only with handwritten BWOR fixtures. It does not include `or_llm_agent` generation.
- The next integration pilot should use both systems: `or_llm_agent` as the producer and OR-CI as the verifier.
- Cost scaling is useful but narrow. It catches objective-coefficient mistakes and does not exercise constraint-side data paths.
- The pilot continuation adds constraint-relaxation metamorphic checks before moving to the integration pilot.

## Actions Taken

- Ran the first OR-CI-only micro-pilot after the Gurobi license was updated.
- Generated the first pilot report at `artifacts/pilot/phase-1-micro-pilot-2026-05-16/report.md`.
- Confirmed all first-pilot expected classifications matched observed classifications.
- Added a constraint-relaxation metadata contract for Phase 1 continuation.
- Added constraint-side wrong fixtures for `BWOR-001`, `BWOR-002`, and `BWOR-010`.
- Updated pytest coverage so constraint-side wrong fixtures must pass cost scaling and fail `constraint_relaxation`.
- Ran the continuation pilot with 21 pytest cases and 12 CLI report runs.
- Generated the continuation report at `artifacts/pilot/phase-1-constraint-relaxation-2026-05-16/report.md`.
- Confirmed all continuation-pilot expected classifications matched observed classifications.
- Started the integration pilot task `05-16-or-ci-integration-pilot`.
- Added a rerunnable integration pilot runner at `artifacts/pilot/phase-1-integration-2026-05-16/run_integration_pilot.py`.
- Ran the first integration attempt with `or_llm_agent` as producer and OR-CI as verifier.
- The attempt is blocked before generated submissions because the configured OpenAI-compatible provider rejected the key. The saved raw provider errors are sanitized.

## Notes

- `SUCCESS` means no configured invariant failed. It is not a proof of full model correctness.
- Constraint relaxation is still a metamorphic check. It improves coverage for selected constraint paths but does not replace larger evaluation or ground-truth comparison in paper-scale experiments.
