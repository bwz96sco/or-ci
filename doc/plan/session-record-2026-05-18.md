# Session Record: Statement-Only Scale Pilot

Date: 2026-05-18

## Scope

- Producer: `or_llm_agent solve-batch --mode agent`
- Verifier: standalone OR-CI through the packaged CLI contract
- Problems: `BWOR-001` through `BWOR-010`
- Input level: natural-language BWOR statements only
- Artifact root:
  `artifacts/pilot/statement-solve-scale-2026-05-18-10case/`

## Actions Taken

- Added `or_llm_agent review-fidelity --mode agent` and
  `review-fidelity-batch --mode agent`.
- Preserved manual review semantics as `accepted` / `rejected`.
- Recorded nested Codex reviewer decisions as `llm_accepted` /
  `llm_rejected` so automated review is distinguishable from human
  certification.
- Ran the 10-case statement-only solve batch:

```bash
uv run or-llm-agent solve-batch \
  --mode agent \
  --ids BWOR-001 BWOR-002 BWOR-003 BWOR-004 BWOR-005 BWOR-006 BWOR-007 BWOR-008 BWOR-009 BWOR-010 \
  --artifact-dir /Users/zhangbowen/Projects/OR/code/or-ci/artifacts/pilot/statement-solve-scale-2026-05-18-10case \
  --codex-timeout-seconds 900
```

- Ran automated source-statement fidelity review:

```bash
uv run or-llm-agent review-fidelity-batch \
  --mode agent \
  --artifact-dir /Users/zhangbowen/Projects/OR/code/or-ci/artifacts/pilot/statement-solve-scale-2026-05-18-10case \
  --codex-timeout-seconds 600
```

## Result

- Final report:
  `artifacts/pilot/statement-solve-scale-2026-05-18-10case/report.md`
- `solve-batch` result: 10 / 10 succeeded.
- OR-CI classification: 10 / 10 `SUCCESS`.
- ProblemSpec validation: 10 / 10 `passed`.
- Model generation: 10 / 10 `generated`.
- Spec repair attempts: every case passed on the first generated spec.
- Automated source-statement fidelity:
  - `llm_accepted`: 9
  - `llm_rejected`: 1

## Fidelity Findings

- `BWOR-003` was rejected by the nested Codex reviewer. The generated spec
  matches the core loan and bond data, but its `bank_deposit_years` omit 2006
  even though the statement says surplus funds may be deposited at the beginning
  of each year.
- `BWOR-007` was accepted with one minor issue: the reviewer noted limited
  metamorphic coverage because only objective coefficient scaling is tested.

## Interpretation

- The scale pilot validates that the statement-only pipeline can generate
  OR-CI-compatible specs and passing Gurobi submissions for a 10-problem BWOR
  batch.
- OR-CI `SUCCESS` remains generated-spec verification, not proof that the
  generated spec fully matches the original statement.
- `BWOR-003` should be manually adjudicated before using its generated spec as
  accepted benchmark metadata. The likely question is whether the omitted 2006
  deposit option is an irrelevant dominated variable or a fidelity mismatch.

## Verification

- `uv run python -m unittest discover` in `or_llm_agent`: 17 passed.
- `uv run python -m compileall src/or_llm_agent tests` in `or_llm_agent`:
  passed.
- `uv run pytest` in `or-ci`: 25 passed.
- `uv run or-ci validate-spec --problem tests/fixtures/bwor/BWOR-001/problem.json`
  in `or-ci`: passed.

## Next Work

- Expand the scale run beyond 10 cases only after deciding how to count
  `llm_accepted` versus human-reviewed `accepted` in the paper metrics.
- Add aggregate runtime and fidelity-review outcome tables if this pilot becomes
  a reported experiment.

## 2026-05-19 Follow-Up

Implemented and ran the automated fidelity-resolution loop:

```bash
uv run or-llm-agent resolve-fidelity-batch \
  --mode agent \
  --artifact-dir /Users/zhangbowen/Projects/OR/code/or-ci/artifacts/pilot/statement-solve-scale-2026-05-18-10case \
  --codex-timeout-seconds 600
```

Result:

- Processed only the rejected case by default: `BWOR-003`.
- Wrote resolution report:
  `artifacts/pilot/statement-solve-scale-2026-05-18-10case/fidelity-resolution-report.md`
- Resolution status: `repaired_accepted`.
- Repaired artifact:
  `artifacts/pilot/statement-solve-scale-2026-05-18-10case/fidelity-resolution/BWOR-003/attempt-1/`
- The repaired ProblemSpec includes `bank_deposit_years` as
  `[2003, 2004, 2005, 2006]`.
- Repaired artifact status: spec validation `passed`, model generation
  `generated`, OR-CI verification `PASS` / `SUCCESS`, fidelity review
  `llm_accepted`.

Updated next work:

- The immediate BWOR-003 mismatch no longer requires manual adjudication for the
  generated repaired artifact.
- Future metrics still need a policy for whether `llm_accepted` can count as
  accepted evidence, or whether paper-grade benchmark metadata requires human
  `accepted`.
