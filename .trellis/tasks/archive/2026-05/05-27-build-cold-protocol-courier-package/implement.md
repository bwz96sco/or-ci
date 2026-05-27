# Implementation Plan

1. Add the courier package builder with generate, `--check`, and `--self-test`
   modes.
2. Generate courier folder artifacts from
   `cold-protocol-send-packet-2026-05-27.json`.
3. Wire the builder check and self-test into the evidence-gate smoke registry.
4. Regenerate the courier and smoke artifacts.
5. Validate courier checks, smoke, paper readiness, pytest, and GitNexus
   detect-changes before committing.
