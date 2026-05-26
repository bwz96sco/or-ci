# Rater Bundle Instruction Card

## Goal

Add a safe, reproducible rater instruction card to the existing human-labeling bundles so the next human-dependent plan step can run with fewer invalid labels and less oral explanation.

## Confirmed Facts

- The active roadmap requires a five-case cold protocol check before the 13-case capstone labels.
- Existing bundles are ready for distribution but their READMEs only summarize contents; they do not enumerate the v2 label vocabulary.
- The frozen addendum defines the required v2 label fields and allowed values.
- Human labels, model responses, mutation outcomes, and adjudication decisions must not be fabricated.

## Requirements

- Generate a `RATER-INSTRUCTIONS.md` file for the cold, capstone, Phase 2 50-case, and NL4OPT rater bundles.
- The instruction card must list the v2 label fields, allowed values, source-underspecification handling, non-claims, and the correct staging/validation path for returned labels.
- The instruction card must be rater-facing only: no coordinator maps, raw artifact roots, prior verdicts, case IDs beyond packet IDs, or source-fidelity reviewer decisions.
- Bundle builders must include and check the instruction card so generated artifacts are reproducible.
- Existing bundle checks and cross-track readiness checks must continue to pass.

## Out Of Scope

- Do not create or fill human label rows.
- Do not promote staged labels into canonical agreement inputs.
- Do not submit baseline prompts or create raw model responses.
- Do not mark mutation seeds accepted or make mutation rows run-eligible.

## Acceptance Criteria

- [ ] Each safe rater bundle contains `RATER-INSTRUCTIONS.md`.
- [ ] Bundle checks fail if the instruction card is missing or stale.
- [ ] The leakage audit still reports zero high-severity issues.
- [ ] Human-labeling handoff and paper evidence-pack readiness still validate.
- [ ] Roadmap or integration notes are updated to point human operators at the instruction cards.
