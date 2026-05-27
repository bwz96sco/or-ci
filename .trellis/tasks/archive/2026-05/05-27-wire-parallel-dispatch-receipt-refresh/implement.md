# Implementation plan

1. Import the receipt recorder follow-up command list in the parallel dispatch
   packet builder.
2. Add `follow_up_commands_after_receipt` to each packet's receipt-recorder
   payload.
3. Render those commands in the Markdown after the receipt row template.
4. Add a self-test assertion that every packet carries the refresh chain.
5. Regenerate/check parallel send packets and smoke artifacts.
6. Verify no evidence state changed, run tests, validate Trellis, run
   GitNexus detect-changes, commit, and archive.
