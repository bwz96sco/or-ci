# Build judge packet contract and audit

## Goal

Implement the next constructed-fault benchmark work package: freeze the LLM
judge packet contract, generate blinded judge packets for the 10 material-valid
pilot mutants, and audit those packets for leakage before any LLM calls.

The user value is to make the next LLM-judge step runnable without letting the
judge see mutation metadata, fault-family labels, materiality labels, or hidden
ground-truth answers.

## Requirements

- Work in the OR-research experiment pack:
  `/Users/zhangbowen/Projects/OR/note/OR-research/experiments/packs/constructed-source-fidelity-fault-benchmark-2026-06-10/`.
- Add a deterministic packet builder script, `build_judge_packets.py`.
- Generate one judge-visible JSON packet per material-valid mutant under
  `judge_packets/`.
- Generate packet support artifacts:
  - `judge_packet_contract.md`
  - `judge_packet_manifest.csv`
  - `judge_packet_audit.md`
  - `judge_packet_audit.json`
- Use anonymous packet IDs that do not include `mutation_id`, fault family, or
  operator names.
- Judge-visible packet JSON may include:
  - original natural-language source statement;
  - candidate ProblemSpec JSON;
  - candidate submission source code;
  - OR-CI report status/classification/checks/failures;
  - instructions and allowed output schema for three judge variants:
    `no_rubric`, `source_fidelity_rubric`, and `evidence_checklist`.
- Judge-visible packet JSON must not include:
  - `mutation_id`;
  - `fault_family`;
  - mutation operator names;
  - mutation metadata paths or metadata content;
  - `denominator_bucket`, `materiality_class`, `oracle_status`;
  - original-vs-mutant objective deltas;
  - source-fidelity oracle decisions;
  - hidden original-source answer labels.
- `judge_packet_manifest.csv` may map anonymous packet IDs to internal mutation
  IDs, but it is not judge-visible.
- `judge_packet_audit.md/json` must prove:
  - 10 packets were generated;
  - each packet has required sections;
  - forbidden leakage tokens are absent from packet content;
  - packet filenames and IDs are anonymous;
  - manifest-only internal fields are separated from judge-visible packet files.
- Add `--check` mode that recomputes expected packet metadata and fails if
  packet files, manifest, contract, or audit are stale.
- Update `03_run_plan.md`, `run_matrix.yaml`, and Stage 06/07 artifacts enough
  to record that the packet contract is frozen and LLM calls are still deferred.
- Use `uv` for Python commands.

## Acceptance Criteria

- [ ] Trellis planning artifacts are complete and validated.
- [ ] `build_judge_packets.py` generates the contract, packet JSON files,
      manifest, and audit artifacts.
- [ ] `build_judge_packets.py --check` passes.
- [ ] Existing acceptance replay check still passes.
- [ ] Research-experiment pack validation passes with
      `--strict-claim-audit`.
- [ ] `uv run pytest` passes in OR-CI.
- [ ] OR-CI package code remains unchanged.
- [ ] GitNexus staged-scope checks run before OR-CI Trellis commits.

## Out Of Scope

- No LLM judge calls.
- No provider/API integration.
- No human labeling.
- No scale-up beyond the existing 10 material-valid mutant denominator.
- No OR-CI verifier changes.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
