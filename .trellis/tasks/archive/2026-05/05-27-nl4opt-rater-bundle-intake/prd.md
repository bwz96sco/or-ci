# Build NL4OPT rater bundle intake

## Goal

Make the frozen NL4OPT 20-case external sanity-check label workflow safe for
human distribution by adding a labeling-operations rater bundle and staged
label-intake gate, matching the capstone and Phase 2 50-case process.

## Confirmed Facts

- The notes repo already has frozen NL4OPT external artifacts under
  `experiments/packs/or-ci-external-sanity-nl4opt-2026-05-26/`.
- The external set has 20 blinded packet files `E001.md` through `E020.md`,
  blank Rater A/B v2 label sheets, and a label-agreement analyzer.
- The current roadmap/reconciliation says NL4OPT must not be distributed
  directly from the external experiment folder; it needs a safe operations
  bundle and label-intake gate first.
- Capstone and Phase 2 already have sibling bundle/intake scripts to follow.

## Requirements

- Add `build_nl4opt_rater_bundle.py` under the labeling-operations experiment.
- Add `build_nl4opt_label_intake.py` under the labeling-operations experiment.
- Build a safe bundle at `nl4opt-rater-bundle-2026-05-27/` containing:
  - 20 packet markdown files copied from the existing blinded packet directory.
  - Blank 20-row Rater A and 20-row Rater B label sheets.
  - A safe in-bundle manifest.
  - A summary JSON and README.
- Build a staged intake directory at `nl4opt-label-intake-2026-05-27/` with
  incoming Rater A/B sheets copied from the safe bundle when missing.
- Generate intake readiness CSV/JSON/Markdown artifacts that report packet
  state, paired completion, partial-row errors, and current status.
- Use the existing NL4OPT v2 label schema validator. Do not invent a divergent
  label schema.
- Validate that rater-facing bundle metadata uses only safe packet IDs and
  in-bundle relative paths.
- Exclude coordinator maps, raw NL4OPT case IDs, absolute paths, prior LLM
  reviewer verdicts, adjudication decisions, baseline artifacts, mutation
  artifacts, and report-ready claims from the safe bundle.
- Wire the new NL4OPT bundle/intake gate into the human-labeling handoff and
  paper evidence-pack readiness scripts.
- Update roadmap/review notes so the next task order points to the generated
  safe NL4OPT bundle and intake gate.

## Acceptance Criteria

- [x] `build_nl4opt_rater_bundle.py` generates and checks the safe 20-packet
      NL4OPT rater bundle.
- [x] `build_nl4opt_label_intake.py` generates and checks staged incoming
      NL4OPT label sheets and readiness artifacts.
- [x] Intake self-test rejects a partially filled label row and accepts a fully
      complete 20-packet paired-label set as adjudication-ready.
- [x] Human-labeling handoff JSON/Markdown includes NL4OPT rater bundle and
      label-intake status.
- [x] Paper evidence-pack readiness includes NL4OPT bundle/intake status and
      keeps `report_ready=false`.
- [x] Roadmap/reconciliation/integration notes identify the safe NL4OPT bundle
      and intake gate as the next external-validity automation task.
- [x] Existing dashboard, handoff, leakage audit, NL4OPT agreement, and paper
      readiness checks still pass.
- [x] Generated artifacts preserve non-claims: no human labels, adjudication,
      source-fidelity accuracy, FAR, baseline, mutation, or external-validity
      claims are created.

## Out Of Scope

- Collecting or fabricating human labels.
- Copying staged labels into canonical agreement files.
- Adjudicating NL4OPT labels.
- Computing external accuracy or FAR metrics.
- Rerunning OR-LLM-Agent or LLM source-fidelity review.
- Changing OR-CI verifier code.
