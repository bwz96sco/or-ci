# Design: Adjudication Operator Runbook

## Context

Label intake and promotion gates exist, but after returns arrive the
coordinator still needs a single post-promotion surface showing which agreement
or adjudication command applies to capstone, Phase 2, and NL4OPT. The current
state must remain blocked because promoted human labels do not exist.

## Approach

Add `build_adjudication_operator_runbook.py` in the labeling operations folder.
It reads existing generated artifacts and emits JSON, CSV, and Markdown. It does
not mutate any evidence files.

Rows include status copied from:

- `label-promotion-readiness-2026-05-27.json`
- dataset intake readiness JSON files
- existing agreement/adjudication summary artifacts

The check mode compares generated artifacts to current expected output. The
self-test asserts blocked current state, exactly three datasets, and no
`--execute` command leakage.

## Non-Goals

- Do not generate labels.
- Do not stage or promote returned sheets.
- Do not adjudicate disagreements.
- Do not compute FAR, accuracy, baseline, mutation, external, or report-ready
  claims.
