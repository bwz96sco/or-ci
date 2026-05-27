# Baseline P007 Judge Captures Design

## Boundary

This task is an evidence-capture slice. It does not change OR-CI source code,
baseline prompt generation logic, label schemas, mutation logic, or direct
strong-LLM policy.

The only experiment rows in scope are:

- `llm_judge_no_rubric/P007`
- `llm_judge_rubric/P007`
- `llm_judge_evidence_checklist/P007`

## Data Flow

1. Use each manual submission bundle as the source prompt for Oracle browser
   mode.
2. Save Oracle's JSON object to the staged response-intake path for that row.
3. Validate staged JSON through the response-intake builder.
4. Promote the row into canonical raw responses and response-template records.
5. Regenerate derived summaries and readiness boards so operator counts match
   the newly captured rows.

## Contracts

- Staged responses must parse with Python `json.loads`.
- Judge-condition outputs keep `mathematical_formulation` and
  `gurobi_python_code` empty.
- `run_id`, `model_or_tool`, and `model_version` are added locally before
  staging so validators can enforce the frozen run policy.
- Failed browser attempts are stored only as failed attempt evidence, never as
  captured responses.

## Rollback

If a row fails validation, remove only the newly staged invalid P007 file for
that row and keep a failed-attempt record. Do not remove earlier P001-P006
captured responses or unrelated notes.
