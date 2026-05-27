# Design

## Scope

The helper copies exactly one operator-supplied returned CSV into one staged
intake target. It is off by default: without `--execute`, it validates and
prints what would happen. It does not run label promotion, adjudication,
protocol-review decisions, mutation promotion, or report-ready transitions.

## Target Registry

The script defines a static registry for the returned-file surfaces:

- cold-check labels;
- capstone rater A/B labels;
- Phase 2 rater A/B labels;
- NL4OPT rater A/B labels;
- mutation seed-review CSV.

Each registry entry records the target path, expected header, expected row
count, expected fixed rater id where applicable, and the follow-up validation
command.

## Validation

For every staging request:

- source path must exist and must not contain placeholder markers;
- source SHA-256 must match when `--source-sha256` is supplied;
- source header must exactly match the target schema;
- source row count must match the registry entry;
- fixed fields such as `rater_id`, `label_schema_version`, `seed_case_id`, and
  `packet_file` must match the target surface where applicable;
- target must be absent or blank/pending only;
- generated readiness CSVs are rejected as source files.

For label sheets, "blank/pending" means no label fields are populated. For
mutation seed review, an absent staged file is blank; a present staged file is
accepted as blank only if every review field is empty.

## Modes

- `--check`: validate registry targets and print count.
- dry-run staging: validate source and target, print source/target/hash and
  follow-up commands, write nothing.
- `--execute`: perform the validated copy.
- `--self-test`: use temporary CSV files to exercise valid and invalid paths.

## Smoke Integration

Add two safe command specs:

- `returned_human_evidence_staging_check`;
- `returned_human_evidence_staging_self_test`.

Both are non-mutating.

## Rollback

Remove the helper, remove the smoke command specs, regenerate the smoke report,
and remove plan-note references.
