# Implementation plan

1. Update `record_human_dispatch_receipt_event.py` follow-up commands to cover
   the full generated surface refresh chain.
2. Add or adjust self-test assertions so the chain cannot regress to ledger
   only.
3. Run the receipt recorder checks and a dry-run send preview.
4. Regenerate/check smoke and affected notes artifacts.
5. Run repository tests, Trellis validation, GitNexus detect-changes, then
   commit notes and archive the Trellis task.

