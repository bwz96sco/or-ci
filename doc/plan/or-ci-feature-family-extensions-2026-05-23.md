# OR-CI Feature Family Extensions Plan

Date: 2026-05-23

## Purpose

Expand OR-CI beyond the current linear LP/MILP verification surface where the
new mathematical family can be represented explicitly and checked
deterministically.

OR-CI means Operations Research Continuous Integration. Its core role is still
CI-style verification for generated optimization submissions. It is not a full
OR modeling process and does not call an LLM.

ModelIR means Optimization Model Intermediate Representation. It is the
normalized view of a solver model used by OR-CI to inspect variables,
constraints, objectives, solver status, and model summary data.

## Baseline

The 82-case agent-mode BWOR pilot produced 21 blocked cases:

- 13 `needs_human` cases.
- 8 `unsupported` cases.

This plan addresses the `unsupported` cases that are blocked by verifier
feature coverage rather than missing or contradictory source information.

Do not broaden OR-CI by accepting vague semantics. Each new family needs an
explicit metadata contract, deterministic verifier behavior, positive tests,
negative tests, and targeted pilot evidence.

## Implementation Result

Implemented on 2026-05-23 in the OR-CI project:

- QP/MIQP quadratic-objective ModelIR extraction and verification support.
- Goal-programming weighted and lexicographic scalarization metadata and
  verifier checks.
- Multi-scenario metadata, scenario solver-status checks, scenario objective
  checks, and scenario-level metamorphic checks.
- OR-CI metadata/report documentation updates.
- Targeted feature-extension pilot artifacts:
  `artifacts/pilot/or-ci-feature-family-extensions-2026-05-23/`.

Verification evidence:

- `uv run pytest -q`: 41 passed.
- `uv run python -m compileall src tests`: passed.
- `uv run python artifacts/pilot/or-ci-feature-family-extensions-2026-05-23/run_feature_extension_pilot.py`: 6 / 6 targeted cases `SUCCESS` / `PASS`.
- `uv run or-ci validate-spec` and `uv run or-ci verify` smoke checks passed
  for the multi-scenario `BWOR-032` artifact.

Consumer-side OR-LLM-Agent prompt coordination remains a downstream integration
task outside this OR-CI implementation.

## Feature Family 1: Quadratic Objective / QP-MIQP

Target cases:

- `BWOR-067`
- `BWOR-071`

Goal:

Support generated Gurobi submissions whose objective contains quadratic terms,
while still rejecting quadratic constraints until they are intentionally added.

Implementation:

- Extend ModelIR extraction to record quadratic objective terms.
- Add allowed problem types `QP` and `MIQP`.
- Report quadratic objective summary in verifier reports.
- Keep quadratic constraints unsupported by default.
- Extend metadata validation so quadratic objective support is explicit.
- Extend cost scaling so configured objective coefficient paths can affect
  quadratic objective terms.
- Keep constraint relaxation behavior unchanged for linear constraints.

Implementation checklist:

- [x] Add ModelIR fields for quadratic objective terms.
- [x] Extract quadratic objective terms from Gurobi models.
- [x] Add `QP` and `MIQP` problem type validation.
- [x] Reject quadratic constraints with a clear classification.
- [x] Add quadratic objective summary to JSON reports.
- [x] Update metadata docs with quadratic objective support.
- [x] Add cost-scaling behavior for quadratic objective cases.

Verification checklist:

- [x] Unit test quadratic objective extraction.
- [x] Unit test linear models still produce the same ModelIR shape as before.
- [x] Unit test quadratic constraints are rejected.
- [x] Unit test QP cost scaling passes on a correct model.
- [x] Unit test QP cost scaling fails on a wrong objective coefficient.
- [x] Run targeted pilot on `BWOR-067`.
- [x] Run targeted pilot on `BWOR-071`.

Report capstone:

- [x] Generate `feature-extension-quadratic-objective-report.md`.
- [x] List targeted cases and recovered cases.
- [x] Show extracted quadratic objective terms.
- [x] Show metamorphic checks run.
- [x] Show remaining unsupported quadratic features.

## Feature Family 2: Goal Programming / Lexicographic Objectives

Target cases:

- `BWOR-012`
- `BWOR-014`
- `BWOR-015`

Goal:

Support goal-programming cases only when the source or clarification artifact
specifies enough semantics to define the achievement function.

Implementation:

- Add explicit goal-programming metadata.
- Support weighted goal achievement when weights are provided.
- Support lexicographic or preemptive priorities when priorities are provided.
- Reject goal-programming cases with missing priorities, missing weights, or
  missing achievement direction.
- Update capability routing expectations so these cases are supported only
  when the required semantics exist.
- Include goal-level objective values in the OR-CI report.

Implementation checklist:

- [x] Add metadata contract for weighted goals.
- [x] Add metadata contract for lexicographic or preemptive goals.
- [x] Add validation for missing weights, priorities, and achievement direction.
- [x] Add report fields for goal-level achieved values.
- [x] Add verifier checks for weighted goal objective value.
- [x] Add verifier checks for lexicographic priority ordering.
- [x] Document the unsupported cases that still require clarification.

Verification checklist:

- [x] Unit test weighted goal-programming metadata validation.
- [x] Unit test lexicographic goal-programming metadata validation.
- [x] Unit test missing weights are rejected.
- [x] Unit test missing priorities are rejected.
- [x] Unit test wrong priority order fails verification.
- [x] Run targeted pilot on `BWOR-012`.
- [x] Run targeted pilot on `BWOR-014`.
- [x] Run targeted pilot on `BWOR-015`.

Report capstone:

- [x] Generate `feature-extension-goal-programming-report.md`.
- [x] List which cases use weighted goals and which use lexicographic goals.
- [x] Show goal achievement values.
- [x] Show rejected ambiguity cases.
- [x] Show recovered cases.

## Feature Family 3: Multi-Scenario / Infeasibility-Plus-Repair

Target case:

- `BWOR-032`

Goal:

Support problems that ask for more than one related model outcome, such as
proving one formulation infeasible and solving a modified formulation.

Implementation:

- Allow one ProblemSpec to define named scenarios.
- Each scenario should have its own instance data, expected solver status, and
  optional objective or metamorphic checks.
- Run OR-CI verification for each scenario separately.
- Aggregate the final classification from all required scenario results.
- Fail the aggregate report if any required scenario has the wrong solver
  status or wrong objective relation.

Implementation checklist:

- [x] Add metadata contract for named scenarios.
- [x] Add scenario-level expected solver status.
- [x] Add scenario-level objective checks.
- [x] Add scenario-level metamorphic checks where applicable.
- [x] Add aggregate scenario report fields.
- [x] Add CLI/report behavior for multi-scenario ProblemSpecs.

Verification checklist:

- [x] Unit test infeasible base scenario passes when expected infeasible.
- [x] Unit test feasible repair scenario passes when expected optimal.
- [x] Unit test wrong scenario solver status fails.
- [x] Unit test aggregate report fails when one required scenario fails.
- [x] Run targeted pilot on `BWOR-032`.

Report capstone:

- [x] Generate `feature-extension-multiscenario-report.md`.
- [x] List scenario names and expected statuses.
- [x] Show actual solver statuses.
- [x] Show objective and metamorphic checks per scenario.
- [x] Show aggregate pass/fail classification.

## Explicitly Postponed Families

Keep these unsupported for now:

- `BWOR-023`: requires verifying a dynamic-programming solution method, not
  just an optimization model.
- `BWOR-061`: stochastic optimal stopping and dynamic policy.
- `BWOR-035`: revisit after clarification because it may require nonlinear or
  probabilistic verification.

Postponed cases should appear in reports as intentional scope limits, not as
unexpected implementation failures.

## Combined Extension Checklist

- [x] Implement quadratic objective support first.
- [x] Implement goal-programming support second.
- [x] Implement multi-scenario support third.
- [x] Update OR-CI metadata documentation.
- [x] Update OR-CI CLI/report documentation.
- [ ] Coordinate OR-LLM-Agent classifier prompts with newly supported families.
- [ ] Coordinate OR-LLM-Agent ProblemSpec prompts with newly supported metadata.
- [x] Run unit tests after each feature family.
- [x] Run targeted blocked-case pilots after each feature family.
- [x] Run one combined blocked-case recovery pilot.

## Combined Report Capstone Checklist

Generate:

```text
or-ci-feature-extension-report.md
or-ci-feature-extension-summary.json
```

The Markdown report must include:

- [x] Baseline unsupported case count.
- [x] Feature families implemented.
- [x] Cases targeted by each family.
- [x] Cases recovered by each family.
- [x] Cases still unsupported.
- [x] Tests run.
- [x] Targeted pilot commands.
- [x] OR-CI report paths.
- [x] Known scope limits.
- [x] Research interpretation of whether the extension strengthens the OR-CI
      core idea or starts a separate verification track.

The summary JSON must include:

- [x] total targeted unsupported cases.
- [x] recovered unsupported cases.
- [x] remaining unsupported cases.
- [x] feature family pass/fail status.
- [x] verifier test status.
- [x] pilot artifact root.

## Success Criteria

- Each supported feature family has an explicit metadata contract.
- OR-CI rejects unsupported mathematical structures with clear classifications.
- Existing LP/MILP behavior remains compatible.
- Each feature family has positive and negative tests.
- Each feature family has at least one targeted pilot case.
- Reports make remaining scope limits clear enough for paper planning.
