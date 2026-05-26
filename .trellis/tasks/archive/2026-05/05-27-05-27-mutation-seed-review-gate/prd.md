# Build mutation seed review gate

## Goal

Create a human-review template and readiness gate for mutation seed candidates,
then wire validated human-accepted seed decisions into mutation queue
eligibility without accepting any seed in the current artifact set.

## Requirements

- Read the immutable `mutation-seed-candidate-manifest-2026-05-26.csv`.
- Generate a human-facing seed review template with one row per candidate seed.
- Keep all current review fields blank/pending.
- Validate any filled review row:
  - require complete decision metadata;
  - allow accepted/rejected/repair decisions only from a fixed vocabulary;
  - require source-fidelity/final-acceptance fields for accepted seeds;
  - forbid accepting seeds that overlap labeled evaluation sets.
- Generate JSON/Markdown readiness reports.
- Update `build_mutation_work_queue.py` so accepted, validated seed reviews can
  make disjoint seed rows run-eligible in future runs.
- Preserve the current state:
  - 29 seed candidates;
  - 0 accepted seeds;
  - 348 mutation queue rows;
  - 0 run-eligible rows.
- Include non-claims: no seed is accepted, no mutant is generated/run, no
  equivalent-mutant decision or recall claim exists.

## Acceptance Criteria

- [x] Seed review builder runs with `uv run python`.
- [x] Current seed review readiness reports 29 pending reviews and 0 accepted
      seeds.
- [x] Partial review metadata fails validation in a self-test.
- [x] Existing mutation seed scaffold check still passes.
- [x] Mutation work queue check still passes with 0 run-eligible rows.
- [x] Mutation generator check still records 0 generated mutants.
- [x] Roadmap/integration/reconciliation notes reference the seed review gate.
- [x] Notes repo is clean after commit.
- [x] Trellis task is archived after verification.

## Out of Scope

- Marking any seed as accepted.
- Editing the immutable candidate manifest.
- Generating mutation artifacts from real seeds.
- Running OR-CI on mutants.
- Reviewing equivalent mutants.
- Computing mutation recall.
