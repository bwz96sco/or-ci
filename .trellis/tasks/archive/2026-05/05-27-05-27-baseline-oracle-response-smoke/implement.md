# Implementation Plan

1. Validate current queue state and identify the selected ready row.
2. Run an Oracle dry run/render for the prompt bundle.
3. Submit the smoke prompt through Oracle browser mode.
4. Parse/save the actual output or record a failure note.
5. Update the response template only if the response JSON validates.
6. Regenerate/check baseline queue and results summaries.
7. Run OR-CI tests, commit notes artifacts, and archive the Trellis task.
