---
name: trellis-local
description: |
  Project-specific Trellis customizations for the OR-CI code workspace.
  This skill documents modifications made to the vanilla Trellis system
  in this project. Inherits from trellis-meta for base documentation.
---

# Trellis Local - OR-CI Code Workspace

## Base Version

Trellis version: 0.6.0-beta.17
Date initialized: 2026-05-15

## Customizations

### Scripts Changed

#### `.trellis/scripts/task.sh`

- Replaced stale generated context paths:
  - `.trellis/spec/shared/index.md` -> `.trellis/spec/guides/index.md`
  - `.trellis/spec/backend/api-module.md` -> `.trellis/spec/backend/directory-structure.md`
  - `.trellis/spec/backend/quality.md` -> `.trellis/spec/backend/quality-guidelines.md`
  - `.trellis/spec/frontend/components.md` -> `.trellis/spec/frontend/component-guidelines.md`
- Fixed `task.sh list` exiting after the first listed task under `set -e` by replacing `((count++))` with `count=$((count + 1))`.

### Workflow Changes

- The `code/or-ci/` repository is used as a coordination-level Git/Trellis project.
- Sibling repositories `../or_llm_agent/` and `../or-exam-dataset/` remain managed by their own Git histories.

## Changelog

### 2026-05-15

- Initialized Git and Trellis under `code/`, then moved the coordination project into `code/or-ci/` after clarifying the intended project root.
- Added OR-CI Phase 1 micro-pilot tasks.
- Patched task context generation and task listing for the generated Trellis version.
