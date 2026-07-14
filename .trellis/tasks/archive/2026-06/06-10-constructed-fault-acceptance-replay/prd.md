# Build acceptance-layer replay for material mutants

## Goal

Implement the next constructed-fault benchmark step: replay acceptance-layer
decisions over the 10 material-valid mutants produced by the materiality oracle
and write traceable layer/family false-accept tables.

The user value is to make the research process visible and executable: instead
of saying "OR-CI may accept wrong-source artifacts," produce concrete tables
showing which acceptance layers accept or reject each material constructed
fault.

## Confirmed Facts

- The OR-research experiment pack is:
  `/Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10/`.
- Prior task generated 15 concrete mutants and classified materiality.
- `materiality_ledger.csv` currently contains 10 `material_valid` mutants, 2
  `silent_or_equivalent` mutants, and 3 invalid/unclassifiable mutants.
- Existing OR-CI reports show 9 of the 10 material-valid mutants have
  `or_ci_status=PASS` / `or_ci_classification=SUCCESS`; one material-valid
  mutant fails OR-CI semantic checks.
- OR-CI package code should remain unchanged for this task. Work should live in
  the OR-research experiment pack and consume existing OR-CI reports.
- The standard research-experiment Stage 05/06 files already exist and must
  remain validator-compatible.

## Requirements

- Add a deterministic replay script in the experiment pack, tentatively
  `run_acceptance_layer_replay.py`.
- Read `materiality_ledger.csv` and restrict primary detector denominators to
  rows with `denominator_bucket=material_valid`.
- Produce per-mutant acceptance decisions for at least these layers:
  - `execution_only`: accepts when the mutant run reaches an optimal solver
    status, regardless source fidelity.
  - `answer_only_mutant_reference`: accepts when the reported objective is
    consistent with the mutant ProblemSpec reference result. This intentionally
    models answer checking against the corrupted artifact, not against hidden
    original-source ground truth.
  - `or_ci_verifier_only`: accepts when OR-CI status is `PASS` and
    classification is `SUCCESS`.
  - `source_fidelity_oracle`: rejects material mutants using the constructed
    mutation oracle. This is a deterministic capstone layer, not an LLM judge or
    human label.
  - `layered_or_ci_plus_source_fidelity`: accepts only when OR-CI and the
    source-fidelity oracle both accept.
- Write acceptance replay outputs:
  - `acceptance_layer_replay_ledger.{csv,json,md}`
  - `acceptance_layer_summary.{csv,json,md}`
  - `acceptance_layer_execution_log.md`
  - acceptance claim/result audit updates that preserve compatibility with
    `validate_experiment_pack.py --strict-claim-audit`
- Update the experiment run plan or claim update to record that LLM judge and
  live full-agent variants remain deferred.
- Provide a `--check` mode that validates:
  - 10 material-valid denominator rows are present;
  - all required layers are present for each material-valid mutant;
  - summary counts match the per-mutant ledger;
  - invalid and silent/equivalent mutants are excluded from the primary
    false-accept denominator;
  - no execution/answer/OR-CI decision depends on mutation metadata fields.
- Use `uv` for Python execution.

## Acceptance Criteria

- [ ] Trellis planning artifacts are complete and validated.
- [ ] `run_acceptance_layer_replay.py` writes the required replay ledgers and
      summaries.
- [ ] `run_acceptance_layer_replay.py --check` passes.
- [ ] Research-experiment validator passes with `--strict-claim-audit`.
- [ ] `uv run pytest` passes in the OR-CI repo.
- [ ] OR-CI code remains unchanged; only Trellis metadata and OR-research note
      artifacts are committed.
- [ ] GitNexus staged-scope checks run before OR-CI Trellis commits.

## Out Of Scope

- No new LLM judge calls.
- No human labeling.
- No modification to OR-CI verifier behavior.
- No scale-up beyond the existing 10 material-valid pilot denominator.
- No claim of natural-distribution false-accept rate.

## Planning Assumption

This task treats the deterministic constructed-fault oracle as the source
fidelity capstone layer. Live LLM rubric judges and full agent re-generation
are deferred until the deterministic replay table is stable.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
