# Cost throughput ledger hardening

## Goal

Harden the 50-case cost/throughput ledger and paper-readiness gate so
machine-observable cost evidence, unpriced-agent limitations, and human-time
blockers are explicit and reproducible.

## Confirmed Facts

- The paper evidence pack still lists the cost/throughput table as partial.
- The current 50-case ledger already records observable session, turn, command,
  file-change, token, solver-call, and solver-check counts.
- The Codex event logs used by the ledger do not contain reliable timestamps in
  the observed sample, so per-case latency cannot be reconstructed from the
  current artifacts.
- The existing cost ledger leaves dollar cost blank because no machine-readable
  price/billing basis is encoded.
- Human label and adjudication minutes cannot exist until human label sheets
  are returned.
- The plan requires cost/throughput evidence, but it must not fabricate pricing
  or imply source-fidelity performance before labels exist.

## Requirements

- Update the cost/throughput ledger generator, not just generated markdown.
- Preserve all existing observable counts.
- Add an explicit cost basis/policy to each row and to the summary:
  - observed token counts are available;
  - no model/billing route is encoded in the per-case Codex event logs;
  - no API price card should be applied without a frozen billing basis;
  - `llm_cost_usd` remains blank until a billing export, explicit price card,
    or defensible subscription amortization policy is supplied.
- Add a machine-cost status that distinguishes unpriced observed usage from
  missing human time.
- Keep human label/adjudication minutes pending.
- Update the paper-readiness generator so the cost table missing-evidence text
  reflects the improved distinction instead of only saying "price card missing."
- Regenerate the 50-case cost ledger and paper evidence pack artifacts.
- Do not create source-fidelity, FAR, baseline-performance, or paper-branch
  claims.

## Acceptance Criteria

- [x] The 50-case cost ledger CSV has explicit cost-basis/status fields.
- [x] The 50-case cost ledger JSON summary records observable machine totals,
      cost-basis policy, and remaining blockers.
- [x] The generated cost ledger markdown explains why token counts are
      reportable but dollars remain non-final.
- [x] Paper evidence pack readiness consumes the updated ledger fields and
      reports the remaining blockers: billing/price basis, reliable latency
      source, human time, and accepted-artifact denominator.
- [x] Cost/throughput, paper-readiness, and next-stage board checks pass.
- [x] `uv run pytest`, code and notes `git diff --check`, task validation, and
      GitNexus change detection pass before archive/commit.
- [x] No final cost-per-accepted-artifact or empirical source-fidelity claim is
      introduced.

## Outcome

- Hardened `build_50case_cost_throughput_ledger.py` so each row records
  event-log row count, timestamped event count, machine usage observation,
  unpriced usage status, cost basis, and cost blocker.
- Regenerated the 50-case cost ledger. It now records 50 cases, 113 Codex
  sessions, 1,735 event-log rows, 0 timestamped event rows, 13,436,477 total
  input+output tokens, 99 solver calls, and 99 solver checks.
- Added a JSON `cost_basis_policy` that permits operational throughput claims
  from observed usage while forbidding dollar or cost-effectiveness claims
  until a billing export, frozen model price card, or subscription amortization
  policy exists and human labels define the denominator.
- Updated paper-readiness generation so the cost table consumes the new ledger
  fields and distinguishes observed machine usage from remaining blockers:
  billing basis, reliable latency source, human labeling/adjudication minutes,
  and accepted-artifact denominator.
- Updated roadmap/reconciliation notes to reflect the hardened partial ledger.

## Verification

- `build_50case_cost_throughput_ledger.py --check`: 50 rows, 113 completed
  turns.
- `build_paper_evidence_pack_readiness.py --check`: 15 sections,
  `status=pending_required_evidence`.
- `build_next_stage_execution_board.py --check`: 8 rows,
  `status=pending_external_evidence_collection`.
- `uv run pytest`: 42 passed.
- Code and notes `git diff --check`: passed.
- `task.py validate`: passed.
- `npx gitnexus detect-changes --repo or-ci --scope all`: no changes detected.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
