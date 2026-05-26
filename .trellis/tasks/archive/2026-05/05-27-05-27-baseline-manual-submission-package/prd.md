# Build manual baseline submission package

## Goal

Generate deterministic manual submission bundles and tracking artifacts for the
52 ready baseline-ablation Oracle prompts without creating model responses.

## Requirements

- Read the existing 52-row `baseline-ablation-run-queue-2026-05-26.csv`.
- Generate one manual submission Markdown bundle per ready row.
- Each bundle must include:
  - queue metadata;
  - the exact queued prompt file content;
  - the output schema;
  - the expected raw response path;
  - instructions to return exactly one JSON object;
  - non-claims that the bundle is not a model result.
- Generate a manual submission manifest CSV/JSON/Markdown summary.
- Do not modify prompt content, create raw response JSON files, or fill response
  decisions.
- Add `--check` validation that generated bundles are in sync with the queue,
  prompt files, and schema.
- Update the roadmap/integration notes to reference the manual package as the
  available fallback while Oracle browser authentication is unresolved.

## Acceptance Criteria

- [x] A builder script exists and runs with `uv run python`.
- [x] 52 manual submission bundles are generated.
- [x] The manifest maps every queue row to a bundle path and expected raw
      response path.
- [x] No `baseline-ablation-raw-responses-2026-05-26/*.json` files are created.
- [x] `--check` validates bundle content and summary freshness.
- [x] Existing baseline run-package/results checks still pass.
- [x] `uv run pytest` for OR-CI still passes.
- [x] Roadmap status is updated without claiming model responses or baseline
      decisions.

## Out of Scope

- Submitting prompts to ChatGPT or Oracle.
- Copying responses from ChatGPT.
- Parsing or validating completed model responses.
- Changing the frozen prompt text or output schema.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
