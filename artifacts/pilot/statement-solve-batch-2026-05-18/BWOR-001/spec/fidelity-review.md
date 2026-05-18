# ProblemSpec Fidelity Review

## Run

- Problem: `BWOR-001`
- Statement file: `/Users/zhangbowen/Projects/OR/code/or-ci/artifacts/pilot/statement-solve-batch-2026-05-18/statements/BWOR-001.txt`
- Generated spec: `spec/problem.json`
- Spec raw output: `raw/spec.txt`
- Spec generation: `generated`
- Spec validation: `passed`
- Model generation: `generated`
- Verification: `PASS`
- Classification: `SUCCESS`
- Fidelity status: `not_reviewed`
- Fidelity gate: `manual_review_required`
- Structured report: `spec/fidelity-review.json`

## Statement Excerpt

```text
A candy factory uses raw materials A, B, and C to produce three different brands of candy: Brand X, Brand Y, and Brand Z. The content proportions of A, B, and C in each brand, the costs of the raw materials, the monthly usage limits for each raw material, as well as the unit processing cost and selling price of each candy brand are shown in Table 1-17.The question is: How many kilograms of each brand of candy should the factory produce each month in order to maximize its profit?Please formulate a linear programming mathematical model for this problem.
\begin{table}[h]
    \centering
    \caption{Raw Materials and Candy Production Data}
    \renewcommand{\arraystretch}{1.2}
    \begin{tabular}{c|ccc|c|c}
        \toprule
        Raw Materials & X & Y & Z & Raw Material Cost(dollar/kg) &...
```

## Automatic Checks

- `PASS` or_ci_spec_validation: spec_validation_status=passed
- `PASS` model_verified_against_generated_spec: verification_status=PASS
- `PENDING` source_statement_fidelity: manual review is required before treating generated spec as ground truth

## Risk Flags

- None detected by automatic checks.

## Manual Checklist

- [ ] Sets and indices in `instance` match the statement.
- [ ] Parameters and numeric values in `instance` match the statement.
- [ ] Objective direction and coefficients match the statement.
- [ ] Constraint families and bounds match the statement.
- [ ] Metamorphic checks touch objective and constraint data paths, where available.
- [ ] OR-CI result is interpreted as verification against the generated spec, not proof of original-statement correctness.

## Reviewer Note

TODO
