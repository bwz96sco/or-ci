# Harden Evidence Progress Gates

## Goal

Make readiness builders tolerate legitimate future human-evidence progress
after cold labels arrive: paper readiness must not require
`primary_next_track=cold_protocol_check` or `total_completed_items=0` forever,
and cold dispatch brief checks must remain valid once the board advances
beyond the cold-check primary action.

## Confirmed Facts

- Current human evidence tracker reports primary next track `cold_protocol_check`
  and 0 completed items.
- Once five cold labels are staged, the tracker should legitimately report
  progress and primary next track `cold_protocol_review`.
- `build_paper_evidence_pack_readiness.py` currently rejects tracker states
  where primary next track is not `cold_protocol_check` or completed items are
  nonzero.
- `build_cold_protocol_dispatch_brief.py` currently rejects an execution board
  whose primary action is no longer `complete_5_cold_check_labels`.
- These checks are correct for the initial state but stale for real progress.

## Requirements

- Allow paper readiness to accept future tracker progress while still rejecting
  impossible or report-ready states before evidence is complete.
- Allow tracker primary next track to advance through the known evidence tracks
  without breaking paper readiness.
- Keep `paper_report_ready=false` and the paper evidence pack `report_ready=false`
  until all required evidence is complete.
- Make the cold dispatch brief validate its own cold distribution/intake facts,
  but stop treating a later board primary action as an error.
- Add self-test coverage for initial tracker state and post-cold-label tracker
  progress.
- Do not fabricate labels, model responses, mutation outcomes, or paper claims.

## Acceptance Criteria

- [ ] Current `--check` commands still pass.
- [ ] Paper readiness self-test covers 0 completed items and >0 completed
  items with non-report-ready status.
- [ ] Cold dispatch brief self-test or check logic allows the board primary
  action to advance after cold labels complete.
- [ ] Current generated outputs preserve: no labels, blank protocol decision,
  capstone blocked, `report_ready=false`.

## Notes

- This patch prepares automation for incoming human evidence; it does not
  create that evidence.
