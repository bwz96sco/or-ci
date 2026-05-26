# Design

## Boundaries

This task modifies notes-vault experiment scripts and generated artifacts. It
does not change OR-CI verifier behavior.

Source artifacts live in:

- `experiments/or-ci-external-sanity-nl4opt-2026-05-26/`

New operations artifacts live in:

- `experiments/or-ci-labeling-operations-2026-05-26/`

The bundle/intake scripts should mirror the established capstone and Phase 2
scripts rather than introduce a new workflow.

## Data Flow

1. `build_nl4opt_rater_bundle.py` reads:
   - external packet index;
   - external packet markdown files;
   - blank NL4OPT Rater A/B v2 label sheets;
   - existing NL4OPT label-agreement validator constants/functions.
2. It writes a safe operations bundle:
   - `packets/E001.md` through `packets/E020.md`;
   - `rater-a-labels.csv`;
   - `rater-b-labels.csv`;
   - `bundle-manifest.csv`;
   - `bundle-summary.json`;
   - `README.md`.
3. `build_nl4opt_label_intake.py` copies the bundle label sheets into a staged
   incoming directory when missing.
4. The intake script validates staged A/B sheets through
   `validate_rater_rows`, reports row states, and gates complete paired labels
   to adjudication readiness without mutating canonical NL4OPT agreement
   artifacts.
5. Handoff/readiness scripts read the new summary and intake JSON files and
   expose their status in existing gate summaries.

## Safety Contract

Rater-facing bundle files may include:

- packet IDs `E001` through `E020`;
- relative in-bundle packet paths;
- blank schema-valid label rows;
- operational instructions and non-claims.

Rater-facing bundle files must not include:

- coordinator packet map;
- raw `NL4OPT-####` case IDs;
- absolute paths or notes-vault source paths;
- prior LLM reviewer verdicts such as `llm_accepted` or `llm_rejected`;
- adjudication, baseline, mutation, or report-ready claims.

## Compatibility

- Reuse `build_nl4opt_label_agreement.py` constants and validators so the
  intake gate stays schema-compatible with the canonical analyzer.
- Keep bundle statuses distinct from capstone and Phase 2 statuses:
  - `ready_for_human_nl4opt_rater_distribution`;
  - `pending_external_nl4opt_labels`;
  - `partial_external_nl4opt_labels_pending`;
  - `invalid_or_partial_external_nl4opt_labels`;
  - `ready_for_external_nl4opt_adjudication`.

## Rollback

All generated files are deterministic. If a generated artifact is wrong, rerun
the corresponding builder after fixing the script. If the bundle is unsafe,
delete the generated bundle/intake artifacts and fix the validation rules
before redistribution.
