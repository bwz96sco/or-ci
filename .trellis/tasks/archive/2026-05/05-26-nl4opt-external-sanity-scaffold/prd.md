# NL4OPT external sanity-check scaffold

## Goal

Freeze the NL4OPT external sanity-check sample, wire it into the OR-CI roadmap, validate reproducible artifacts, and record the next executable tasks.

## User Value

The reviewed OR-CI research roadmap needs one external sanity-check source
that is frozen before model outputs are inspected. This task turns the Claude
and GPT-5.5 Pro review recommendation into a reproducible notes artifact so
the project can run the external test later without cherry-picking cases or
tuning the pipeline on the external set.

## Confirmed Facts

- The main roadmap is
  `/Users/zhangbowen/Projects/OR/note/OR-research/ideas/or-ci-next-stage-research-roadmap-2026-05-26.md`.
- Claude review requested an external sanity check such as NL4OPT, ComplexOR,
  MAMO, or a held-out BWOR split.
- GPT-5.5 Pro review recommended NL4OPT when the paper emphasizes
  natural-language-to-optimization formulation.
- The local NL4OPT source file is available at
  `/Users/zhangbowen/Projects/OR/code/or_llm_agent/data/datasets/NL4OPT_with_optimal_solution.json`.
- The external scaffold should live in the notes vault, not in OR-CI verifier
  package code.
- The external run itself is model-run-dependent and should not be faked by
  placeholder outputs.
- Human source-fidelity labels are still required before accuracy claims.

## Requirements

- Create a notes-vault experiment directory for the NL4OPT external
  sanity-check scaffold.
- Freeze `NL4OPT` as the first external source for this roadmap branch.
- Select exactly 20 external cases by a deterministic pre-output rule.
- Preserve a full selection audit over every eligible local NL4OPT row.
- Export a clean JSONL dataset and statement files suitable for
  `or-llm-agent solve-batch`.
- Write a runbook that forbids prompt, rubric, threshold, or solver-policy
  tuning on the external cases.
- Update the next-stage roadmap so Task 13 reflects the frozen sample and the
  remaining pending run/review/label/report work.
- Update the review-integration note so the Claude and Pro response
  disposition points to the NL4OPT scaffold.
- Keep NL4OPT results separate from BWOR metrics unless task definitions are
  proven compatible before external outcomes are inspected.
- Verify the generator/checker with `uv` and keep generated Python cache files
  out of the worktree.

## Acceptance Criteria

- [x] `experiments/packs/or-ci-external-sanity-nl4opt-2026-05-26/` exists in the
      notes vault with a README, manifest generator, audit files, selected
      manifest, case ID list, clean JSONL dataset, runbook, and 20 statement
      files.
- [x] The selected sample is reproducible from the local source dataset using
      the documented hash rule.
- [x] The manifest status makes clear that model execution, source-fidelity
      review, blinded packets, human labels, and the final external report are
      still pending.
- [x] The roadmap links to the frozen manifest/runbook and marks Task 13 as
      selected/frozen but not executed.
- [x] The review-integration note records that NL4OPT was chosen because it
      matches the paper's natural-language-to-optimization framing.
- [x] `uv run python build_nl4opt_external_manifest.py --check` passes from
      the external scaffold directory.
- [x] `uv run python -m py_compile build_nl4opt_external_manifest.py` passes
      from the external scaffold directory.
- [x] `git diff --check` passes in the notes repo.
- [x] OR-CI package code remains unchanged.

## Out of Scope

- Running the 20 external NL4OPT model-generation jobs.
- Running `source_fidelity_v1` on the external artifacts.
- Creating external blinded rater packets.
- Entering human/expert labels or adjudication.
- Claiming an external false-accept rate or pooling NL4OPT into BWOR headline
  metrics.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
