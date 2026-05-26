# Build guarded label promotion gate

## Goal

Add a guarded promotion gate that can move staged returned human-label sheets
from labeling-operations intake directories into the canonical agreement input
files only after the relevant intake gate proves the labels are complete and
valid.

## Confirmed Facts

- Capstone, Phase 2 50-case, and NL4OPT intake gates exist and currently have
  0 complete label pairs.
- Canonical agreement analyzers read their own rater CSVs from the source
  experiment directories, not from the staged intake directories.
- Current intake gates intentionally do not copy staged labels into canonical
  agreement files.
- The next human-dependent work will return label sheets through the staged
  intake directories, so a guarded promotion step is needed before agreement
  and adjudication outputs can advance.

## Requirements

- Add a deterministic promotion-readiness script under the labeling-operations
  experiment.
- Cover all three current staged-label datasets:
  - 13-case capstone.
  - Phase 2 50-case pilot.
  - NL4OPT 20-case external sanity check.
- For each dataset, report:
  - intake status;
  - completed rater counts;
  - paired completion count;
  - issue count;
  - staged source CSVs;
  - canonical target CSVs;
  - whether promotion is currently allowed;
  - the exact promotion command to run after labels are complete.
- The default/generate/check path must be read-only with respect to canonical
  agreement inputs.
- A promotion path must require an explicit `--execute --dataset <id>` and must
  refuse to copy when the intake gate is not adjudication-ready.
- Promotion must not invent labels, adjudication decisions, agreement metrics,
  source-fidelity accuracy, FAR, baseline, mutation, or external-validity
  claims.
- Wire promotion readiness into human-labeling handoff and paper evidence-pack
  readiness.

## Acceptance Criteria

- [x] Promotion readiness CSV/JSON/Markdown are generated and checked.
- [x] All current datasets are reported as blocked/pending because no labels
      are complete.
- [x] `--execute --dataset <id>` refuses to copy under current pending intake
      states.
- [x] Handoff and paper readiness include the promotion gate.
- [x] Existing bundle/intake/dashboard/handoff/paper checks still pass.
- [x] No canonical rater CSV changes are made while intake gates are pending.

## Out Of Scope

- Collecting or fabricating human labels.
- Adjudicating labels.
- Running agreement analyzers after real labels.
- Computing source-fidelity metrics.
- Changing OR-CI verifier code.
