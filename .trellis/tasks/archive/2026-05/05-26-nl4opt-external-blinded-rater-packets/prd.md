# NL4OPT external blinded rater packets

## Goal

Generate blinded rater packets and blank label sheets for the completed 20-case NL4OPT external sanity-check artifact root.

## User Value

The external NL4OPT run is now complete, but its LLM source-fidelity judgments
are not human ground truth. This task prepares the external artifacts for
independent human labeling without exposing case IDs, artifact paths, OR-CI
classifications, LLM fidelity verdicts, or prior reviewer notes to raters.

## Confirmed Facts

- The frozen sample and run live under
  `/Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/or-ci-external-sanity-nl4opt-2026-05-26`.
- Raw generated artifacts live under
  `/Users/zhangbowen/Projects/OR/code/or-ci/artifacts/pilot/external-sanity-nl4opt-20case-2026-05-26`.
- The frozen external run summary is committed in notes commit `9751871`.
- The human-labeling addendum requires blinded rater packets and separation of
  LLM reviewer evidence from human ground truth.
- For a 20-case external sanity check, all packets should be double-labeled if
  possible; partial overlap is not needed at this size.

## Requirements

- Generate exactly 20 rater-facing packet markdown files from the frozen
  NL4OPT selected case order.
- Use external packet IDs only (`E001` ... `E020`) in rater-facing materials.
- Include source statement, generated formal artifact when present, generated
  code when present, and neutral solver diagnostics without verdict fields.
- Preserve blocked/missing-artifact cases as rater packets without fabricating
  generated artifacts.
- Keep a coordinator-only packet map that links packet IDs back to case IDs,
  paths, OR-CI classification, and LLM fidelity status.
- Generate blank Rater A, Rater B, and adjudication CSVs using the v2
  source-fidelity label schema.
- Validate that rater-facing packets do not leak raw case IDs, artifact paths,
  LLM verdicts, source-fidelity review terms, or OR-CI classification terms.
- Update the external experiment README and roadmap status after generation.

## Acceptance Criteria

- [x] `build_nl4opt_blinded_rater_packets.py` exists and supports `--check`.
- [x] `external-sanity-nl4opt-blinded-rater-packets-2026-05-26/` contains
      `README.md`, `packet-index.csv`, and exactly 20 `E*.md` packets.
- [x] `external-sanity-nl4opt-blinded-rater-packet-map-2026-05-26.json`
      exists and is coordinator-only.
- [x] Rater A and Rater B blank CSVs each contain 20 rows.
- [x] The adjudication blank CSV contains 20 rows.
- [x] Rater-facing packet checks reject leaked case IDs, artifact paths, LLM
      verdicts, fidelity-review paths, and OR-CI classification terms.
- [x] `uv run python build_nl4opt_blinded_rater_packets.py --check` passes.
- [x] `uv run python -m py_compile build_nl4opt_blinded_rater_packets.py`
      passes.
- [x] `git diff --check` passes in the notes repo.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
