# Implementation Plan

1. [x] Dry-run Oracle bundle assembly for P002.
2. [x] Run Oracle browser mode with `gpt-5.5-pro`, remote Chrome if needed, and an
   output file under the attempts directory.
3. [x] Inspect the Oracle session/result for model-selection evidence.
4. [x] Parse the final answer as JSON.
5. [x] If valid and Extended Pro-compliant, stage the JSON at
   `baseline-ablation-response-intake-2026-05-27/direct_strong_llm/P002.json`.
   Not applicable: the answer was invalid JSON and resolved ordinary `Pro`.
6. [x] If invalid/noncompliant, write an attempt failure note and do not stage.
7. [x] Run:
   - `build_baseline_response_intake.py --check`
   - `build_baseline_response_capture.py --check`
   - `build_baseline_response_operator_queue.py --check`
   - paper/board checks if generated gate state changes.
8. [x] Commit notes evidence and archive the Trellis task.
