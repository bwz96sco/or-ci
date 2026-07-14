# Implementation Plan

1. [x] Confirm the current baseline queue state for `direct_strong_llm/P002`.
2. [x] Dry-run the Oracle prompt bundle for token/file sanity.
3. [x] Run Oracle browser mode with:
   - `--model gpt-5.5-pro`
   - `--browser-model-strategy select`
   - `--browser-thinking-time extended`
   - `--remote-chrome 127.0.0.1:61836`
   - strict JSON wrapper prompt
4. [x] Inspect the Oracle session log and metadata for model and thinking-time
   evidence.
5. [x] Parse the saved output as JSON.
6. [x] If valid and policy-compliant:
   - add staged metadata;
   - write the staged response JSON;
   - run intake checks.
   Not applicable: the saved output was invalid JSON.
7. [x] If invalid or policy-noncompliant:
   - write a retry failure note;
   - ensure no staged/canonical response exists for P002.
8. [x] Run validation:
   - `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-self-host-exploration-2026-05-25/build_baseline_response_intake.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-self-host-exploration-2026-05-25/build_baseline_response_capture.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-self-host-exploration-2026-05-25/build_baseline_response_operator_queue.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-paper-evidence-pack-2026-05-27/build_paper_evidence_pack_readiness.py --check`
   - `PYTHONDONTWRITEBYTECODE=1 uv run python experiments/packs/or-ci-paper-evidence-pack-2026-05-27/build_next_stage_execution_board.py --check`
   - `uv run pytest`
   - `git diff --check`
   - `git -C /Users/zhangbowen/Projects/OR/note/OR-research diff --check`
   - `npx gitnexus detect-changes --repo or-ci --scope all`
9. [x] Commit notes evidence and archive the Trellis task.
