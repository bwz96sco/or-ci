# Session Record: OR-CI Project Setup

Date: 2026-05-15

## Decisions

- The OR-CI coordination project lives at `code/or-ci`, not at `code`.
- The implementation target was initially recorded as `code/or_llm_agent`, but the clarified architecture is that OR-CI should be a standalone package in `code/or-ci`.
- `code/or_llm_agent` should consume OR-CI as a package or CLI dependency rather than own the OR-CI implementation.
- Trellis task PRDs and planning documents live in `code/or-ci`.
- New OR-CI work should use BWOR naming only.
- Phase 1 uses JSON metadata, not YAML.
- Phase 1 uses handwritten fixtures for `BWOR-001`, `BWOR-002`, and `BWOR-010`.
- Phase 1 supports Gurobi linear models only.
- The verifier must not pass `evaluation_only.answer` or labels into `build_model`.
- Cost scaling checks solver status and scaled objective value only; it must not assert identical variable assignments.

## Actions Taken

- Initialized Git and Trellis in `code/or-ci`.
- Created OR-CI Trellis tasks for:
  - Phase 1 parent micro-pilot
  - data contracts and CLI report
  - Gurobi ModelIR extractor
  - cost-scaling verifier
  - BWOR micro-pilot fixtures
  - pytest and CLI acceptance
- Set `05-15-or-ci-phase-1-micro-pilot` as the current Trellis task.
- Validated all new OR-CI Trellis task context files.
- Added standalone coding plan at `doc/plan/or-ci-phase-1-micro-pilot.md`.

## Notes

- The mempal MCP server failed with a database schema mismatch, so mempal recording was performed through the local `mempal` CLI.
