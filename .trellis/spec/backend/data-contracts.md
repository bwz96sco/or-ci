# Data Contracts

> Public data contracts that flow across OR-CI module boundaries: problem metadata, submission interface, ModelIR, and verification report.

---

## Overview

(To be filled — describe the boundary-crossing types: input problem metadata JSON, the `build_model(data)` submission contract, the in-memory ModelIR, and the output verification report JSON.)

---

## Problem Metadata Schema

(To be filled — document required top-level fields, the `instance` subtree, the `metamorphic.cost_scaling` block (Phase 1a), the emerging `metamorphic.constraint_relaxation` block (2026-05-16 continuation: configured numeric instance paths to relax), and the `evaluation_only` carve-out that must never reach `build_model`.)

---

## Submission Contract

(To be filled — describe the exact `build_model(data: dict) -> gurobipy.Model` signature, side-effect rules, and what `data` is allowed to contain.)

---

## ModelIR

(To be filled — variables, objective, constraints, summary counts; how Gurobi attributes map onto IR fields; what counts as "unsupported feature".)

---

## Report JSON

(To be filled — top-level fields, classification taxonomy, failure entries, possible_causes; what passing means and does NOT mean.)

---

## Metamorphic Checks Catalog

(To be filled — one row per supported check:
- **cost_scaling** (Phase 1a, fully specified): scales configured objective-coefficient instance paths by a positive factor; invariant on objective value.
- **constraint_relaxation** (2026-05-16 continuation, emerging — no implementation PRD yet): relaxes configured numeric instance paths used in constraint RHS or bounds; invariant on optimal objective being weakly better after relaxation.

For each check: metadata sub-schema, the invariant it asserts, the classification it emits on violation, and what must NOT be asserted.)

---

## Canonical Vocabulary

(To be filled — single authoritative spelling of: problem_id, classification enum values, status, solver_status, sense names, vtype names, BWOR naming. All other spec files MUST use these exact strings.)
