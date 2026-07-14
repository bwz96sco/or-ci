# Design: Constructed Fault Pilot Inventory

## Scope

The implementation lives in the OR-research notes experiment pack, not inside
the OR-CI verifier package:

`/Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10/`

It reads local artifacts and writes deterministic planning artifacts. No solver
execution, mutation generation, OR-CI invocation, network access, or LLM calls
are in scope.

## Inputs

- Experiment contract:
  `01_experiment_contract.md`
- Run matrix:
  `run_matrix.yaml`
- Prior mutation seed manifest and related scaffolds:
  `../or-ci-self-host-exploration-2026-05-25/mutation-*.{csv,json,md}`
- Existing 82-case artifact root:
  `/Users/zhangbowen/Projects/OR/code/or-ci/artifacts/pilot/statement-solve-scale-2026-05-22-82case/`

Input readers should tolerate missing optional files by recording unavailable
evidence fields instead of crashing, but required source tables must fail fast.

## Scripts

### `build_seed_inventory.py`

Builds one row per candidate seed. It resolves case IDs, source statements,
ProblemSpec paths, executable/submission artifacts, OR-CI reports, solver/result
signals, and reference-answer signals. Eligibility is explicit and reproducible:
rows are `eligible`, `ineligible`, or `review_needed` with a reason list.

The script writes:

- `seed_inventory.csv`
- `seed_inventory.json`
- `seed_inventory.md`

### `build_fault_family_applicability.py`

Reads eligible seed rows and classifies each seed against the five pilot
source-fidelity fault families:

- `omitted_action_index_or_year`
- `dropped_constraint_family`
- `objective_coefficient_swap`
- `unit_scaling_break`
- `scenario_or_temporal_omission`

The classifier uses structural evidence from ProblemSpec keys, prior mutation
family mappings, and statement text tokens. It should distinguish
`applicable`, `not_applicable`, and `needs_manual_targeting`.

The script writes:

- `fault_family_applicability.csv`
- `fault_family_applicability.json`
- `fault_family_applicability.md`

### `build_pilot_mutation_plan.py`

Reads the inventory and applicability matrix, chooses a deterministic 3-5 seed
pilot set, and emits planned seed-family rows. The plan names future mutation
targets and artifact paths but keeps every row `artifact_write_status =
not_written_planning_only`.

The script writes:

- `pilot_mutation_plan.csv`
- `pilot_mutation_plan.json`
- `pilot_mutation_plan.md`

## Shared Implementation Pattern

Use the existing prior mutation scripts as style references:

- `argparse` with `--check`
- stdlib `csv`, `json`, `pathlib`
- stable JSON formatting: `indent=2`, `sort_keys=True`, trailing newline
- deterministic ordering by case ID/family
- Markdown summaries as report-facing explainers

Do not introduce a shared utility module unless the third script repeats enough
non-trivial logic that a local helper clearly reduces risk.

## Non-Claims

Every summary must preserve these boundaries:

- no independent human label evidence;
- no human-calibrated source-fidelity accuracy;
- no natural-distribution rate;
- no OR-CI source-fidelity proof;
- no materiality/detection claim before future solver/comparator stages.

## Risks

- Existing artifacts may not expose solver/reference-answer fields uniformly.
  Mitigation: record traceable evidence availability separately from final
  eligibility.
- Prior mutation family names do not perfectly match the new source-fidelity
  taxonomy. Mitigation: map only defensible families and mark the rest as
  `needs_manual_targeting`.
- Some planned rows may not be material after solve comparison. Mitigation:
  keep the plan as candidate rows only and require the future materiality
  oracle before detection metrics.
