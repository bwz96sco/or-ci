# ProblemSpec Fidelity Review

## Run

- Problem: `BWOR-010`
- Statement file: `/Users/zhangbowen/Projects/OR/code/or-ci/artifacts/pilot/statement-solve-smoke-2026-05-17/statements/BWOR-010.txt`
- Generated spec: `spec/problem.json`
- Spec raw output: `raw/spec.txt`
- Spec generation: `generated`
- Spec validation: `failed`
- Model generation: `skipped`
- Verification: `skipped`
- Classification: `skipped`
- Fidelity status: `not_reviewed`

## Statement Excerpt

```text
A city has three flour mills, which supply flour to three food processing factories. The output of each flour mill, the processing capacity of each food factory, and the unit transportation cost between each flour mill and food factory are shown in Table 3-31. It is assumed that the profit per unit of flour processed into food is: Factory 1: 12 yuan, Factory 2: 16 yuan, Factory 3: 11 yuan, All flour mills and food factories are managed by the same administrative body. Objective: Determine a flour allocation plan that maximizes total benefit, considering both transportation costs and unit profits.

\begin{table}[h]
    \centering
    \caption{Table 3-31: Transportation Cost Between Flour Mills and Food Processing Plants}
    \renewcommand{\arraystretch}{1.2}
    \begin{tabular}{c|ccc|c}...
```

## Manual Checklist

- [ ] Sets and indices in `instance` match the statement.
- [ ] Parameters and numeric values in `instance` match the statement.
- [ ] Objective direction and coefficients match the statement.
- [ ] Constraint families and bounds match the statement.
- [ ] Metamorphic checks touch objective and constraint data paths, where available.
- [ ] OR-CI result is interpreted as verification against the generated spec, not proof of original-statement correctness.

## Reviewer Note

TODO
