# Design: LLM Judge Result Finalization

## Boundary

This task updates research-experiment tooling and artifacts only. OR-CI package
logic remains unchanged.

## Data Flow

```text
llm_judge_responses/*.json
llm_judge_oracle_logs/*.log
  -> run_llm_judge_pilot.py
  -> llm_judge_results.csv
  -> llm_judge_summary.{csv,json,md}
  -> llm_judge_oracle_log_summary.{csv,json,md}
  -> results_ledger.csv / claim_ledger.csv / claim_update.md
```

## Result Semantics

The constructed denominator is material by construction. For each valid LLM
judge response:

- `final_acceptance=accepted` is a false accept;
- `final_acceptance=rejected` is detected;
- `final_acceptance=indeterminate` is neither accepted nor detected.

The primary paper-facing comparison should be per variant on 10 packets, not
the aggregate 30-response total, because the 30 total repeats the same 10
packets under three judging variants.

## Provider Caveat

Oracle logs are external execution evidence. They can support browser route,
session ID, elapsed time, token estimate, saved output, and model label printed
by Oracle. They do not prove the ChatGPT UI picker state when logs say
`verified=no`.

## Rollback

Regeneration is idempotent and rewrites only LLM judge summary/log-summary
artifacts plus research ledgers.
