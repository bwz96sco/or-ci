# OR-CI BWOR Micro-Pilot Fixtures

## Goal

Create controlled handwritten metadata and submission fixtures for the Phase 1 BWOR micro-pilot.

## Required Problems

- `BWOR-001`: blending LP, maximization, candy factory.
- `BWOR-002`: blending LP, minimization, feed mix.
- `BWOR-010`: transportation/profit LP, maximization, flour allocation.

## Fixture Requirements

For each BWOR problem, provide:

- one `problem.json` metadata file
- one correct submission with `build_model(data)`
- one syntax/runtime-error submission
- one runnable-but-wrong submission

At least one runnable-but-wrong fixture must be detectable by cost scaling. Other wrong fixtures may demonstrate that cost scaling has limited coverage.

## Metadata Rules

- Put structured data under `instance`.
- Put cost-scaling metadata under `metamorphic.cost_scaling`.
- Put answer/label information only under `evaluation_only`.
- Do not use NL4OR names in new fixture paths, identifiers, comments, or test names.

## Acceptance Criteria

- All correct fixtures solve to optimal status.
- Error fixtures fail during import or `build_model`.
- At least one wrong fixture violates the cost-scaling invariant.
- Fixtures are small enough to be read and debugged by hand.
