# OR-CI Data Contracts and CLI Report

## Goal

Create the v1 OR-CI package skeleton, public data contracts, CLI entrypoint, and report schema needed by later tasks.

## Implementation Requirements

- Work in this standalone OR-CI repo.
- Add package `or_ci` with modules for models/contracts, metadata loading, report serialization, submission loading, and CLI wiring.
- Add `[project.scripts]` entrypoint so `uv run or-ci verify ...` invokes the verifier.
- Use standard-library JSON for metadata; do not add PyYAML.
- Add pytest as a dev/test dependency if the project does not already have it.

## Required Interfaces

- Submission contract:
  ```python
  def build_model(data: dict) -> gurobipy.Model:
      ...
  ```
- CLI:
  ```bash
  uv run or-ci verify --problem path/to/problem.json --submission path/to/model.py --out path/to/report.json
  ```
- Metadata shape:
  ```json
  {
    "id": "BWOR-002",
    "problem_type": "LP",
    "instance": {},
    "metamorphic": {
      "cost_scaling": {
        "coefficient_paths": ["instance.price"],
        "factors": [2.0],
        "tolerance_abs": 1e-6,
        "tolerance_rel": 1e-6
      }
    },
    "evaluation_only": {
      "answer": 32.43,
      "label": "correct"
    }
  }
  ```

## Report Requirements

The report JSON must include:

- `problem_id`
- `submission`
- `status`
- `classification`
- `solver_status`
- `model_ir_summary`
- `checks`
- `failures`
- `possible_causes`

Do not include claims that the model is fully correct. Passing means no tested invariant failed.

## Acceptance Criteria

- CLI argument parsing validates required paths and writes JSON to `--out`.
- `evaluation_only` fields are retained in loaded metadata but never passed to `build_model`.
- Initial tests cover metadata loading, report serialization, and CLI argument validation.
