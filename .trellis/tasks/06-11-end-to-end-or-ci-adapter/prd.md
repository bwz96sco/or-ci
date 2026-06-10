# End-to-end OR-CI adapter for problem statement to answer evidence

## Goal

Add a deterministic OR-CI evidence-pack adapter that links a source problem statement, structured OR-CI problem metadata, a submitted `build_model(data)` file, and the verifier report into one reusable JSON artifact.

This is the first OR-CI code step toward the research goal "problem statement -> answer evidence", without adding LLM generation, network calls, or source-statement parsing into OR-CI.

## Confirmed Facts

- OR-CI is a Python CLI verifier in `src/or_ci`.
- The existing CLI has `verify` and `validate-spec`.
- `verify` loads structured problem metadata, imports a submitted `build_model(data)` function, runs deterministic checks, and writes a JSON report.
- OR-CI must not add LLM provider code, network calls, prompt code, or `or_llm_agent` imports.
- OR-CI uses BWOR naming in code/tests/fixtures; do not add NL4OPT/NL4OR names to OR-CI code or tests.
- Research evidence already shows that OR-CI `PASS` is verifier evidence, not source-statement fidelity proof.

## Requirements

- Add a CLI subcommand that creates an evidence-pack JSON artifact from:
  - `--statement`: path to a source problem statement file.
  - `--problem`: path to OR-CI problem metadata JSON.
  - `--submission`: path to a submitted Python model file.
  - `--out`: path for the evidence-pack JSON.
- The command must internally run the existing verifier path rather than duplicating verifier logic.
- The evidence pack must include:
  - schema/version marker.
  - statement path, existence status, SHA-256 hash, and byte size.
  - problem metadata path, problem id, problem type, SHA-256 hash, and byte size.
  - submission path, SHA-256 hash, and byte size.
  - embedded OR-CI verification report dict.
  - answer evidence derived only from verifier-observed solver/report fields.
  - explicit source-fidelity boundary/non-claims.
- The command must not:
  - parse natural-language statements into models.
  - call LLMs or network services.
  - import from `or_llm_agent`.
  - claim source-statement correctness from OR-CI `PASS`.
  - include full submission source text in the pack.

## Acceptance Criteria

- [ ] `uv run or-ci evidence-pack --statement <txt> --problem <json> --submission <py> --out <json>` writes a stable JSON evidence pack.
- [ ] The embedded verification report has the same top-level report schema as `or-ci verify`.
- [ ] A passing fixture produces `verification_status == "PASS"` and answer evidence from the original solver status/objective where available.
- [ ] A missing statement path fails at the CLI boundary with a clear message and does not write a pack.
- [ ] Tests cover the new CLI command and evidence-pack structure.
- [ ] `uv run pytest` passes.
- [ ] OR-CI code remains deterministic and contains no LLM/provider/network integration.

## Out Of Scope

- Natural-language parsing.
- Automatic model generation.
- Source-fidelity judging.
- NL4OPT/NL4OR fixture names in OR-CI.
- Full SWE-agent orchestration.
- Research-note report generation.

## Open Questions

None blocking the MVP. Stronger source-fidelity review or producer integration should be a later task.
