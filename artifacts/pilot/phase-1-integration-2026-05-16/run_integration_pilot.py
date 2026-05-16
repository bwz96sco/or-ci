from __future__ import annotations

import argparse
import asyncio
import contextlib
import io
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_OR_CI_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OR_LLM_AGENT_ROOT = DEFAULT_OR_CI_ROOT.parent / "or_llm_agent"
sys.path.insert(0, str(DEFAULT_OR_LLM_AGENT_ROOT))

from or_llm_eval_async_resilient import async_query_llm


DEFAULT_IDS = ("BWOR-001", "BWOR-002", "BWOR-010")


def main() -> None:
    args = parse_args()
    asyncio.run(run(args))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the OR-LLM-Agent -> OR-CI integration pilot.")
    parser.add_argument("--model", default="o3-mini", help="Model name routed by or_llm_agent.")
    parser.add_argument("--ids", nargs="+", default=list(DEFAULT_IDS), help="BWOR ids to run.")
    parser.add_argument("--reuse-submissions", action="store_true", help="Skip LLM generation when submission exists.")
    parser.add_argument("--or-ci-root", type=Path, default=DEFAULT_OR_CI_ROOT)
    parser.add_argument("--or-llm-agent-root", type=Path, default=DEFAULT_OR_LLM_AGENT_ROOT)
    parser.add_argument("--artifact-dir", type=Path, default=Path(__file__).resolve().parent)
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    artifact_dir = args.artifact_dir.resolve()
    submissions_dir = artifact_dir / "submissions"
    raw_dir = artifact_dir / "raw"
    reports_dir = artifact_dir / "reports"
    submissions_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    records = load_bwor_records(args.or_llm_agent_root / "data" / "datasets" / "bwor.jsonl")
    rows = []

    for problem_id in args.ids:
        problem_path = args.or_ci_root / "tests" / "fixtures" / "bwor" / problem_id / "problem.json"
        submission_path = submissions_dir / f"{problem_id}.py"
        raw_path = raw_dir / f"{problem_id}.txt"
        report_path = reports_dir / f"{problem_id}.json"

        generation_status = "reused"
        generation_error = ""
        if not args.reuse_submissions or not submission_path.exists():
            generation_status, generation_error = await generate_submission(
                problem_id=problem_id,
                record=records[problem_id],
                problem_path=problem_path,
                submission_path=submission_path,
                raw_path=raw_path,
                model=args.model,
            )

        verification = verify_submission(
            or_llm_agent_root=args.or_llm_agent_root,
            problem_path=problem_path,
            submission_path=submission_path,
            report_path=report_path,
        )
        row = {
            "problem_id": problem_id,
            "model": args.model,
            "generation_status": generation_status,
            "generation_error": generation_error,
            "submission": str(submission_path.relative_to(artifact_dir)),
            "raw_response": str(raw_path.relative_to(artifact_dir)),
            "report": str(report_path.relative_to(artifact_dir)),
            **verification,
        }
        rows.append(row)
        print(f"{problem_id}: generation={generation_status} classification={row.get('classification')}")

    summary = summarize(rows)
    (artifact_dir / "summary.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_markdown_report(artifact_dir / "report.md", args, summary, rows)
    print(f"wrote {artifact_dir / 'report.md'}")


async def generate_submission(
    *,
    problem_id: str,
    record: dict[str, Any],
    problem_path: Path,
    submission_path: Path,
    raw_path: Path,
    model: str,
) -> tuple[str, str]:
    problem = json.loads(problem_path.read_text(encoding="utf-8"))
    messages = [
        {
            "role": "system",
            "content": (
                "You are an operations research modeling code generator. "
                "Produce a single Python module that implements the OR-CI submission contract."
            ),
        },
        {
            "role": "user",
            "content": build_prompt(problem_id, record, problem),
        },
    ]
    provider_log = io.StringIO()
    with contextlib.redirect_stdout(provider_log):
        success, response = await async_query_llm(messages, model_name=model)
    response = sanitize_error_text(response)
    captured_log = sanitize_error_text(provider_log.getvalue())
    raw_path.write_text(captured_log + response, encoding="utf-8")
    if not success:
        submission_path.write_text("# generation failed before Python code was produced\n", encoding="utf-8")
        return "failed", response

    code = extract_python_code(response)
    submission_path.write_text(code.rstrip() + "\n", encoding="utf-8")
    if "def build_model" not in code:
        return "generated_without_build_model", "response did not contain def build_model"
    return "generated", ""


def build_prompt(problem_id: str, record: dict[str, Any], problem: dict[str, Any]) -> str:
    return f"""Problem id: {problem_id}

Natural language problem:
{record["en_question"]}

OR-CI instance data passed to build_model(data):
```json
{json.dumps(problem["instance"], ensure_ascii=False, indent=2)}
```

Metamorphic verifier configuration:
```json
{json.dumps(problem["metamorphic"], ensure_ascii=False, indent=2)}
```

Write one Python module with exactly this public contract:

```python
import gurobipy as gp
from gurobipy import GRB

def build_model(data: dict) -> gp.Model:
    ...
```

Rules:
- Return an unoptimized gurobipy.Model.
- Do not call optimize().
- Do not print output.
- Do not read files, call APIs, or use external packages other than gurobipy.
- Do not hard-code the known optimal objective value or solution.
- Use the values in data, not copied constants, so transformed OR-CI data changes the model.
- Do not use evaluation_only fields; they are not passed to build_model.
- Output only a fenced python code block.
"""


def extract_python_code(text: str) -> str:
    matches = re.findall(r"```(?:python)?\s*([\s\S]*?)```", text)
    if matches:
        return matches[-1].strip()
    return text.strip()


def sanitize_error_text(text: str) -> str:
    text = re.sub(r"(invalid key:\s*)[^'\"\\s,)]+", r"\1<redacted>", text)
    return text


def verify_submission(
    *,
    or_llm_agent_root: Path,
    problem_path: Path,
    submission_path: Path,
    report_path: Path,
) -> dict[str, Any]:
    result = subprocess.run(
        [
            "uv",
            "run",
            "or-ci",
            "verify",
            "--problem",
            str(problem_path),
            "--submission",
            str(submission_path),
            "--out",
            str(report_path),
        ],
        cwd=or_llm_agent_root,
        capture_output=True,
        text=True,
        check=False,
    )
    verification: dict[str, Any] = {
        "verify_returncode": result.returncode,
        "verify_stdout": result.stdout,
        "verify_stderr": result.stderr,
        "classification": "VERIFY_COMMAND_FAILED",
        "status": "FAIL",
        "failure_check": "",
    }
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        verification.update(
            {
                "classification": report["classification"],
                "status": report["status"],
                "failure_check": report["failures"][0]["check"] if report["failures"] else "",
                "checks": [check["name"] + ":" + check["status"] for check in report["checks"]],
            }
        )
    return verification


def load_bwor_records(path: Path) -> dict[str, dict[str, Any]]:
    records = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            records[record["id"]] = record
    return records


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    classifications: dict[str, int] = {}
    generation_statuses: dict[str, int] = {}
    for row in rows:
        classifications[row["classification"]] = classifications.get(row["classification"], 0) + 1
        generation_statuses[row["generation_status"]] = generation_statuses.get(row["generation_status"], 0) + 1
    return {
        "total": len(rows),
        "classifications": classifications,
        "generation_statuses": generation_statuses,
    }


def write_markdown_report(path: Path, args: argparse.Namespace, summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    matrix = [
        "| Problem | Generation | OR-CI Classification | Failure Check | Submission | Report |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        matrix.append(
            f"| {row['problem_id']} | `{row['generation_status']}` | `{row['classification']}` | "
            f"`{row['failure_check'] or '-'}` | `{row['submission']}` | `{row['report']}` |"
        )

    current_result = (
        "BLOCKED: `or_llm_agent` reached the provider but no Python submissions were generated. "
        "See `summary.json` and `raw/*.txt` for sanitized provider errors."
        if summary["generation_statuses"].get("failed") == summary["total"]
        else "COMPLETED: at least one generated submission reached OR-CI verification."
    )

    path.write_text(
        f"""# OR-CI Integration Pilot Report

Date: 2026-05-16

## Scope

- Producer: `or_llm_agent`
- Verifier: standalone OR-CI CLI through the editable `or-ci` dependency
- Model: `{args.model}`
- Problems: {", ".join(args.ids)}

## Summary

{current_result}

```json
{json.dumps(summary, ensure_ascii=False, indent=2)}
```

## Matrix

{chr(10).join(matrix)}

## Interpretation Notes

- `SUCCESS` means the generated submission passed the configured OR-CI invariants, not full model correctness.
- Semantic failures distinguish which verifier invariant failed first.
- Generation failures are reported separately from OR-CI classifications.
""",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
