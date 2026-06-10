# Design

## Architecture

Add a small deterministic evidence-pack layer beside the existing report layer:

- `src/or_ci/evidence_pack.py`
  - owns evidence-pack JSON shape, path hashing, answer-evidence extraction, and `write_evidence_pack`.
- `src/or_ci/cli.py`
  - adds an `evidence-pack` subcommand.
  - validates input paths.
  - delegates verification to `or_ci.verifier.verify`.
  - delegates evidence-pack construction/writing to `or_ci.evidence_pack`.

This keeps `verifier.py` unchanged and avoids duplicating model execution or report serialization.

## Data Flow

```text
statement.txt
problem.json ─┐
submission.py ├─ or_ci.verifier.verify(...) -> VerificationReport -> report dict
              └─ evidence_pack.build_evidence_pack(...) -> evidence_pack.json
```

## Evidence-Pack Shape

Top-level fields:

- `schema_version`: string, initially `or_ci_evidence_pack_v1`.
- `source_statement`: path/hash/size/existence metadata.
- `problem_metadata`: path/hash/size plus `problem_id` and `problem_type`.
- `submission`: path/hash/size metadata.
- `verification_report`: `VerificationReport.to_dict()`.
- `answer_evidence`: derived from the verifier report.
- `source_fidelity_boundary`: explicit non-claim text.

`answer_evidence` should be conservative:

- `verification_status`
- `classification`
- `original_solver_status`
- `original_objective_value` when present
- `answer_available`: true only when original objective evidence is present

## Boundaries

- The statement file is retained as provenance only. OR-CI does not parse it.
- The pack does not assert source fidelity.
- The pack may support later reviewer/judge code, but does not implement a judge.
- The pack does not write a separate OR-CI verification report unless a future task adds an optional flag.

## Compatibility

- Existing `verify` and `validate-spec` commands stay unchanged.
- Existing report JSON schema stays unchanged.
- No new runtime dependencies.
- Existing tests should continue to pass.

## Risks

- Users could overread an evidence pack as a source-fidelity proof. Mitigation: include explicit boundary/non-claim fields and test for them.
- Adding path hashes could create unstable output if absolute paths vary. The pack stores paths as provided/resolved consistently and hashes file content for durable identity.
- Verification can fail due to metadata or submission issues. Submission-level failures should still produce an evidence pack because the embedded report is evidence; missing CLI input files should fail before pack creation.
