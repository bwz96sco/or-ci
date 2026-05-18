# ProblemSpec Fidelity Review

## Run

- Problem: `BWOR-002`
- Statement file: `/Users/zhangbowen/Projects/OR/code/or-ci/artifacts/pilot/statement-solve-batch-2026-05-18/statements/BWOR-002.txt`
- Generated spec: `spec/problem.json`
- Spec raw output: `raw/spec.txt`
- Spec generation: `generated`
- Spec validation: `passed`
- Model generation: `generated`
- Verification: `PASS`
- Classification: `SUCCESS`
- Fidelity status: `accepted`
- Fidelity gate: `accepted`
- Structured report: `spec/fidelity-review.json`

## Review Decision

- Status: `accepted`
- Reviewer: `Codex`
- Reviewed at: `2026-05-18T02:12:07+00:00`
- Note: Manual review against BWOR statements accepted: sets, numeric parameters, objective sense and coefficients, constraints, and metamorphic paths are faithful for BWOR-001, BWOR-002, and BWOR-010. OR-CI PASS is still interpreted as verification against the reviewed generated spec.

## Evidence

- artifacts/pilot/statement-solve-batch-2026-05-18/report.md
- artifacts/pilot/statement-solve-batch-2026-05-18/summary.json

## Statement Excerpt

```text
A livestock farm raises animals for sale. It is required that each animal must receive at least 700g of protein, 30g of minerals, and 100mg of vitamins per day. There are five types of feed available for selection. The nutritional content per kilogram and the unit price of each type of feed are shown in Table 1-22.

\begin{table}[h]
    \centering
    \caption{Nutritional Content and Price of Feed}
    \renewcommand{\arraystretch}{1.2}
    \begin{tabular}{c|c|c|c|c}
        \toprule
        Feed & Protein (g) & Minerals (g) & Vitamins (mg) & Price (dollar/kg) \\
        \midrule
        1 & 3 & 1.0 & 0.5 & 0.2 \\
        2 & 2 & 0.5 & 1.0 & 0.7 \\
        3 & 1 & 0.2 & 0.2 & 0.4 \\
        4 & 6 & 2.0 & 2.0 & 0.3 \\
        5 & 18 & 0.5 & 0.8 & 0.8 \\
        \bottomrule
    \end{tabula...
```

## Automatic Checks

- `PASS` or_ci_spec_validation: spec_validation_status=passed
- `PASS` model_verified_against_generated_spec: verification_status=PASS
- `PASS` source_statement_fidelity: manual review accepted: Manual review against BWOR statements accepted: sets, numeric parameters, objective sense and coefficients, constraints, and metamorphic paths are faithful for BWOR-001, BWOR-002, and BWOR-010. OR-CI PASS is still interpreted as verification against the reviewed generated spec.

## Risk Flags

- None detected by automatic checks.
