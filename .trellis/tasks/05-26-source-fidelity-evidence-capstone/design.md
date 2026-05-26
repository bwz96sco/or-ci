# Source Fidelity Evidence Capstone Design

## Boundaries

- OR-CI code remains untouched.
- OR-LLM-Agent code should remain unchanged unless the evidence run exposes a bug.
- Generated review artifacts under `artifacts/pilot/...` are local evidence outputs and may be gitignored.
- Report-facing Markdown/JSON in the OR research note directory is the durable user-facing output.

## Evidence Plan

Use the latest full BWOR batch root:

`/Users/zhangbowen/Projects/OR/code/or-ci/artifacts/pilot/or-llm-agent-full-bwor-2026-05-25`

Run `or-llm-agent review-fidelity-batch --mode agent` only for high-value baseline case IDs:

- Direct baseline successes: `BWOR-001`, `BWOR-016`, `BWOR-051`, `BWOR-067`, `BWOR-071`, `BWOR-082`.
- Boundary blocked cases: `BWOR-020`, `BWOR-027`, `BWOR-061`.

Then run `or-llm-agent review-fidelity --mode agent` on selected clarified artifacts:

- `clarified/BWOR-014/attempt-1`
- `clarified/BWOR-015/attempt-2`
- `clarified/BWOR-027/attempt-1`
- `clarified/BWOR-046/attempt-1`

## Output Contract

Baseline batch root should contain:

- `fidelity-rubric-summary.json`
- `fidelity-rubric-report.md`

Experiment directory should contain:

- `source-fidelity-rubric-capstone-2026-05-26.json`
- `source-fidelity-rubric-capstone-2026-05-26.md`
- README updates that cite the new capstone.

## Interpretation

The capstone must report reviewed baseline cases separately from clarified/provisional cases. Provisional clarified cases cannot be counted as human-certified source-faithful successes.
