# Design

## Boundary

This task owns one retry attempt for `direct_strong_llm/P002`. It may write:

- an Oracle attempt output text file;
- a failure note if the attempt is invalid or policy-noncompliant;
- a staged response JSON only if the answer is valid JSON and Extended Pro
  evidence is sufficient.

It must not write canonical raw responses directly and must not update paper
claims.

## Acceptance Path

1. Oracle saves the final assistant answer to an attempt text file.
2. The Oracle session log is inspected for:
   - model-selection evidence resolving Pro;
   - `Thinking time: Extended` selection evidence.
3. The saved answer is parsed as JSON.
4. If valid, staged metadata is added without changing substantive decision
   fields.
5. The staged JSON is written to:
   `baseline-ablation-response-intake-2026-05-27/direct_strong_llm/P002.json`.
6. `build_baseline_response_intake.py --check` must classify the row as
   promotable before any promotion is considered.

## Failure Path

If any gate fails, the answer remains attempt evidence only. The failure note
must state:

- row identity;
- attempt output path;
- Oracle session id;
- model-selection and thinking-time evidence;
- JSON parse or validator result;
- confirmation that no staged or canonical response was written.

## JSON Wrapper Control

The retry prompt reinforces JSON syntax without changing the source task:

- return exactly one JSON object;
- no Markdown fences;
- parseable by Python `json.loads`;
- escape quotes and newlines inside string fields;
- `gurobi_python_code` must be a JSON string, not raw code.

## Rollback

If a staged response is written but validation fails, delete only that staged
file and replace it with a failure note. The attempt output remains preserved.
