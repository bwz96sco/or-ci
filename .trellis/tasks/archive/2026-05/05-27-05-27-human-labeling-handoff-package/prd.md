# Build human labeling handoff package

## Goal

Generate a deterministic, human-facing handoff package for the immediate
labeling gates in the OR-CI next-stage research plan, starting with the
5-packet cold protocol check.

## Requirements

- Read the existing labeling dispatch queue.
- Generate a compact cold-check handoff CSV and Markdown note listing exactly
  the five cold protocol assignments.
- Generate a structured JSON summary of the current labeling gates:
  - cold protocol check;
  - 13-case capstone labeling/adjudication;
  - 50-case evidence-source decision and labeling;
  - NL4OPT external labeling;
  - mutation seed review and baseline response blockers.
- Include explicit non-claims:
  - no labels are created;
  - no adjudication outcomes are inferred;
  - no baseline model responses are inferred;
  - no mutation execution is enabled.
- Include `--check` validation that the generated files are in sync with the
  current dispatch queue and referenced source artifacts.
- Update roadmap/integration notes to reference the handoff package as the next
  executable human-labeling gate.

## Acceptance Criteria

- [x] Builder script runs with `uv run python`.
- [x] Cold-check handoff has exactly 5 pending `cold_rater` rows.
- [x] Handoff summary reports 229 dispatch assignments and 0 completed labels.
- [x] Generated files do not modify any rater/adjudication label CSVs.
- [x] `--check` validates generated artifacts.
- [x] Roadmap/integration/reconciliation notes point to the new handoff package.
- [x] Notes repo is clean after commit.
- [x] Trellis task is archived after verification.

## Out of Scope

- Filling any label or adjudication field.
- Choosing the 50-case evidence-source decision.
- Submitting baseline prompts to Oracle/ChatGPT.
- Creating raw baseline responses.
- Marking mutation seeds as accepted.
