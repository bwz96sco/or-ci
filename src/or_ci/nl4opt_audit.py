from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable

import gurobipy as gp
from gurobipy import GRB


class NL4OPTError(ValueError):
    pass


WORD_NUMBERS = {
    "zero": 0.0,
    "one": 1.0,
    "two": 2.0,
    "three": 3.0,
    "four": 4.0,
    "five": 5.0,
    "six": 6.0,
    "seven": 7.0,
    "eight": 8.0,
    "nine": 9.0,
    "ten": 10.0,
    "eleven": 11.0,
    "twelve": 12.0,
    "thirteen": 13.0,
    "fourteen": 14.0,
    "fifteen": 15.0,
    "sixteen": 16.0,
    "seventeen": 17.0,
    "eighteen": 18.0,
    "nineteen": 19.0,
    "twenty": 20.0,
    "half": 0.5,
    "third": 1.0 / 3.0,
    "a third": 1.0 / 3.0,
    "twice": 2.0,
    "thrice": 3.0,
}

STATUS_NAMES = {
    GRB.LOADED: "loaded",
    GRB.OPTIMAL: "optimal",
    GRB.INFEASIBLE: "infeasible",
    GRB.INF_OR_UNBD: "infeasible_or_unbounded",
    GRB.UNBOUNDED: "unbounded",
    GRB.CUTOFF: "cutoff",
    GRB.ITERATION_LIMIT: "iteration_limit",
    GRB.NODE_LIMIT: "node_limit",
    GRB.TIME_LIMIT: "time_limit",
    GRB.SOLUTION_LIMIT: "solution_limit",
    GRB.INTERRUPTED: "interrupted",
    GRB.NUMERIC: "numeric",
    GRB.SUBOPTIMAL: "suboptimal",
}


@dataclass(frozen=True)
class OfficialTarget:
    source_id: str
    payload: dict[str, Any]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise NL4OPTError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise NL4OPTError(f"{path}:{line_number}: expected JSON object")
            rows.append(row)
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def load_official_targets(path: Path) -> list[OfficialTarget]:
    targets: list[OfficialTarget] = []
    for line_number, outer in enumerate(read_jsonl(path), start=1):
        if len(outer) != 1:
            raise NL4OPTError(f"{path}:{line_number}: expected one source-id key")
        source_id, payload = next(iter(outer.items()))
        if not isinstance(payload, dict) or not isinstance(payload.get("document"), str):
            raise NL4OPTError(f"{path}:{line_number}: malformed target payload")
        targets.append(OfficialTarget(source_id=str(source_id), payload=payload))
    source_ids = [target.source_id for target in targets]
    if len(source_ids) != len(set(source_ids)):
        raise NL4OPTError("official source IDs are not unique")
    return targets


def normalize_statement(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def _canonical_answer(value: Any) -> tuple[str, float | None]:
    text = str(value).strip()
    lowered = text.lower()
    if lowered in {"no best solution", "no solution", "infeasible", "unbounded"}:
        return "no_best_solution", None
    try:
        number = float(text.replace(",", ""))
    except ValueError:
        return lowered, None
    if math.isclose(number, -99999.0, rel_tol=0.0, abs_tol=1e-9):
        return "no_best_solution", None
    return "numeric", number


def answers_equal(left: Any, right: Any, *, tolerance: float = 1e-7) -> bool:
    left_kind, left_number = _canonical_answer(left)
    right_kind, right_number = _canonical_answer(right)
    if left_kind != right_kind:
        return False
    if left_kind != "numeric":
        return True
    assert left_number is not None and right_number is not None
    return math.isclose(left_number, right_number, rel_tol=tolerance, abs_tol=tolerance)


def parse_number(raw: Any, *, ratio: bool = False) -> float:
    text = str(raw).strip().lower().replace(",", "")
    is_percent = "%" in text or "percent" in text
    text = text.replace("$", "").replace("%", "").replace("percent", "").strip()
    if text.endswith(" times"):
        text = text[: -len(" times")].strip()
    if text in WORD_NUMBERS:
        value = WORD_NUMBERS[text]
    else:
        try:
            value = float(text)
        except ValueError as exc:
            raise NL4OPTError(f"unsupported numeric value: {raw!r}") from exc
    if is_percent or (ratio and value > 1.0):
        value /= 100.0
    return value


def _direction_sense(direction: str) -> int:
    normalized = direction.lower()
    if "max" in normalized:
        return GRB.MAXIMIZE
    if any(token in normalized for token in ("min", "reduce", "decrease", "lowest")):
        return GRB.MINIMIZE
    raise NL4OPTError(f"unsupported objective direction: {direction!r}")


def _canonical_variable(payload: dict[str, Any], raw_name: str) -> str:
    variables = [str(name) for name in payload.get("vars", [])]
    if raw_name in variables:
        return raw_name
    mention_map = payload.get("var_mention_to_first_var", {})
    mapped = mention_map.get(raw_name) if isinstance(mention_map, dict) else None
    if mapped in variables:
        return str(mapped)
    normalized = normalize_statement(raw_name)
    candidates = [name for name in variables if normalize_statement(name) == normalized]
    if len(candidates) == 1:
        return candidates[0]
    raise NL4OPTError(f"cannot map variable mention {raw_name!r} to {variables!r}")


def _linear_expression(
    payload: dict[str, Any],
    terms: dict[str, Any],
    variables: dict[str, gp.Var],
) -> gp.LinExpr:
    coefficients: dict[str, float] = {}
    for raw_name, raw_coefficient in terms.items():
        name = _canonical_variable(payload, str(raw_name))
        coefficients[name] = coefficients.get(name, 0.0) + parse_number(raw_coefficient)
    return gp.quicksum(coefficient * variables[name] for name, coefficient in coefficients.items())


def _add_relation(model: gp.Model, lhs: gp.LinExpr | gp.Var, operator: str, rhs: Any, name: str) -> None:
    if operator == "LESS_OR_EQUAL":
        model.addConstr(lhs <= rhs, name=name)
    elif operator == "GREATER_OR_EQUAL":
        model.addConstr(lhs >= rhs, name=name)
    else:
        raise NL4OPTError(f"unsupported operator: {operator!r}")


def build_target_model(payload: dict[str, Any], *, domain: str) -> tuple[gp.Model, dict[str, gp.Var]]:
    if domain not in {"continuous", "integer"}:
        raise NL4OPTError(f"unsupported domain: {domain!r}")
    variable_names = [str(name) for name in payload.get("vars", [])]
    if not variable_names:
        raise NL4OPTError("target has no variables")

    model = gp.Model("nl4opt_target")
    model.Params.OutputFlag = 0
    model.Params.DualReductions = 0
    model.Params.InfUnbdInfo = 1
    variable_type = GRB.CONTINUOUS if domain == "continuous" else GRB.INTEGER
    variables = {
        name: model.addVar(lb=0.0, vtype=variable_type, name=f"x_{index}")
        for index, name in enumerate(variable_names)
    }

    objective = payload.get("obj_declaration")
    if not isinstance(objective, dict):
        raise NL4OPTError("target has no objective declaration")
    if "terms" in objective:
        objective_expression = _linear_expression(payload, objective["terms"], variables)
    elif "vars" in objective:
        names = [_canonical_variable(payload, str(name)) for name in objective["vars"]]
        objective_expression = gp.quicksum(variables[name] for name in names)
    else:
        raise NL4OPTError("unsupported objective declaration")
    model.setObjective(objective_expression, _direction_sense(str(objective.get("direction", ""))))

    declarations = payload.get("const_declarations", [])
    if not isinstance(declarations, list):
        raise NL4OPTError("constraint declarations must be a list")
    for index, declaration in enumerate(declarations):
        if not isinstance(declaration, dict):
            raise NL4OPTError(f"constraint {index} is not an object")
        constraint_type = declaration.get("type")
        operator = str(declaration.get("operator", ""))
        name = f"c_{index}_{constraint_type}"
        if constraint_type == "linear":
            lhs = _linear_expression(payload, declaration.get("terms", {}), variables)
            rhs = parse_number(declaration.get("limit"))
        elif constraint_type == "sum":
            lhs = gp.quicksum(variables.values())
            rhs = parse_number(declaration.get("limit"))
        elif constraint_type in {"lowerbound", "upperbound"}:
            variable_name = _canonical_variable(payload, str(declaration.get("var", "")))
            lhs = variables[variable_name]
            rhs = parse_number(declaration.get("limit"))
        elif constraint_type == "xy":
            x_name = _canonical_variable(payload, str(declaration.get("x_var", "")))
            y_name = _canonical_variable(payload, str(declaration.get("y_var", "")))
            lhs = variables[x_name]
            rhs = variables[y_name]
        elif constraint_type == "xby":
            x_name = _canonical_variable(payload, str(declaration.get("x_var", "")))
            y_name = _canonical_variable(payload, str(declaration.get("y_var", "")))
            multiplier = parse_number(declaration.get("param"))
            lhs = variables[x_name]
            rhs = multiplier * variables[y_name]
        elif constraint_type == "ratio":
            variable_name = _canonical_variable(payload, str(declaration.get("var", "")))
            fraction = parse_number(declaration.get("limit"), ratio=True)
            lhs = variables[variable_name]
            rhs = fraction * gp.quicksum(variables.values())
        else:
            raise NL4OPTError(f"unsupported constraint type: {constraint_type!r}")
        _add_relation(model, lhs, operator, rhs, name)
    model.update()
    return model, variables


def solve_target(payload: dict[str, Any], *, domain: str) -> dict[str, Any]:
    try:
        model, variables = build_target_model(payload, domain=domain)
        model.optimize()
        status_code = int(model.Status)
        status = STATUS_NAMES.get(status_code, f"status_{status_code}")
        result: dict[str, Any] = {
            "domain": domain,
            "status": status,
            "status_code": status_code,
            "objective": None,
            "variables": {},
            "max_constraint_violation": None,
            "iis_constraints": [],
        }
        if status_code == GRB.OPTIMAL:
            result["objective"] = float(model.ObjVal)
            result["variables"] = {name: float(variable.X) for name, variable in variables.items()}
            try:
                result["max_constraint_violation"] = float(model.ConstrVio)
            except gp.GurobiError:
                pass
        elif status_code == GRB.INFEASIBLE:
            model.computeIIS()
            result["iis_constraints"] = [constraint.ConstrName for constraint in model.getConstrs() if constraint.IISConstr]
        return result
    except (NL4OPTError, gp.GurobiError) as exc:
        return {
            "domain": domain,
            "status": "parse_or_solver_error",
            "status_code": None,
            "objective": None,
            "variables": {},
            "max_constraint_violation": None,
            "iis_constraints": [],
            "error": f"{type(exc).__name__}: {exc}",
        }


def solve_official_targets(targets: Iterable[OfficialTarget]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for target in targets:
        rows.append(
            {
                "source_id": target.source_id,
                "document_sha256": sha256_text(str(target.payload["document"])),
                "continuous": solve_target(target.payload, domain="continuous"),
                "integer": solve_target(target.payload, domain="integer"),
            }
        )
    return rows


def map_benchmark_rows(
    historical_rows: list[dict[str, Any]],
    corrected_rows: list[dict[str, Any]],
    official_targets: list[OfficialTarget],
    *,
    overrides: dict[str, str] | None = None,
    minimum_similarity: float = 0.85,
) -> list[dict[str, Any]]:
    if len(historical_rows) != len(corrected_rows):
        raise NL4OPTError("historical and corrected snapshots have different row counts")
    overrides = overrides or {}
    official_by_id = {target.source_id: target for target in official_targets}
    normalized_official = {
        target.source_id: normalize_statement(str(target.payload["document"])) for target in official_targets
    }
    mappings: list[dict[str, Any]] = []
    for index, (historical, corrected) in enumerate(zip(historical_rows, corrected_rows, strict=True)):
        historical_question = str(historical.get("en_question", ""))
        corrected_question = str(corrected.get("en_question", ""))
        normalized_historical = normalize_statement(historical_question)
        normalized_corrected = normalize_statement(corrected_question)
        candidates: list[tuple[float, str, str]] = []
        for source_id, official_text in normalized_official.items():
            historical_score = SequenceMatcher(None, normalized_historical, official_text).ratio()
            corrected_score = SequenceMatcher(None, normalized_corrected, official_text).ratio()
            if corrected_score > historical_score:
                candidates.append((corrected_score, source_id, "corrected_question"))
            else:
                candidates.append((historical_score, source_id, "historical_question"))
        candidates.sort(reverse=True)
        best_score, best_source_id, basis = candidates[0]
        second_score = candidates[1][0]
        override_source_id = overrides.get(str(index)) or overrides.get(f"nl4opt-row-{index + 1:04d}")
        overridden = bool(override_source_id)
        if override_source_id:
            if override_source_id not in official_by_id:
                raise NL4OPTError(f"row {index}: unknown override source ID {override_source_id!r}")
            best_source_id = override_source_id
            basis = "manual_override"
            official_text = normalized_official[best_source_id]
            best_score = max(
                SequenceMatcher(None, normalized_historical, official_text).ratio(),
                SequenceMatcher(None, normalized_corrected, official_text).ratio(),
            )
        accepted = overridden or best_score >= minimum_similarity
        mappings.append(
            {
                "row_id": f"nl4opt-row-{index + 1:04d}",
                "dataset_index_zero": index,
                "dataset_row_number": index + 1,
                "source_id": best_source_id,
                "match_basis": basis,
                "similarity": round(best_score, 9),
                "second_similarity": round(second_score, 9),
                "similarity_margin": round(best_score - second_score, 9),
                "manual_override": overridden,
                "accepted": accepted,
            }
        )
    accepted_ids = [mapping["source_id"] for mapping in mappings if mapping["accepted"]]
    duplicates = sorted(source_id for source_id in set(accepted_ids) if accepted_ids.count(source_id) > 1)
    if duplicates:
        raise NL4OPTError(f"row mapping is not one-to-one; duplicate source IDs: {duplicates}")
    return mappings


def prepare_pilot(
    *,
    official_path: Path,
    historical_path: Path,
    corrected_path: Path,
    output_dir: Path,
    official_commit: str,
    corrected_commit: str,
    seed: str,
    control_count: int,
    expected_answer_changes: int,
    overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    official_targets = load_official_targets(official_path)
    historical_rows = read_jsonl(historical_path)
    corrected_rows = read_jsonl(corrected_path)
    mappings = map_benchmark_rows(
        historical_rows,
        corrected_rows,
        official_targets,
        overrides=overrides,
    )
    unresolved = [mapping for mapping in mappings if not mapping["accepted"]]
    if unresolved:
        row_ids = ", ".join(mapping["row_id"] for mapping in unresolved)
        raise NL4OPTError(f"unresolved source mappings: {row_ids}")

    changed_indices = [
        index
        for index, (historical, corrected) in enumerate(zip(historical_rows, corrected_rows, strict=True))
        if str(historical.get("en_answer")) != str(corrected.get("en_answer"))
    ]
    if len(changed_indices) != expected_answer_changes:
        raise NL4OPTError(
            f"expected {expected_answer_changes} answer changes, observed {len(changed_indices)}"
        )
    unchanged_candidates = [
        index
        for index, (historical, corrected) in enumerate(zip(historical_rows, corrected_rows, strict=True))
        if historical.get("en_question") == corrected.get("en_question")
        and str(historical.get("en_answer")) == str(corrected.get("en_answer"))
    ]
    ranked_controls = sorted(
        unchanged_candidates,
        key=lambda index: sha256_text(f"{seed}:{mappings[index]['row_id']}"),
    )
    if len(ranked_controls) < control_count:
        raise NL4OPTError(f"requested {control_count} controls, only {len(ranked_controls)} available")
    control_indices = ranked_controls[:control_count]
    selected = [(index, "answer_changed") for index in changed_indices]
    selected.extend((index, "unchanged_control") for index in control_indices)

    official_by_id = {target.source_id: target.payload for target in official_targets}
    source_manifest: list[dict[str, Any]] = []
    hidden_answers: list[dict[str, Any]] = []
    for index, selection_group in selected:
        mapping = mappings[index]
        row_id = mapping["row_id"]
        statement = str(historical_rows[index]["en_question"]).rstrip() + "\n"
        statement_path = output_dir / "source" / "statements" / f"{row_id}.txt"
        statement_path.parent.mkdir(parents=True, exist_ok=True)
        statement_path.write_text(statement, encoding="utf-8")
        target_path = output_dir / "source" / "formal-targets" / f"{row_id}.json"
        target_payload = {
            "row_id": row_id,
            "source_id": mapping["source_id"],
            "official_target": official_by_id[mapping["source_id"]],
        }
        write_json(target_path, target_payload)
        source_manifest.append(
            {
                "row_id": row_id,
                "split": "pilot_evidence",
                "statement_path": str(statement_path.relative_to(output_dir)),
                "source_sha256": sha256_file(statement_path),
            }
        )
        hidden_answers.append(
            {
                "row_id": row_id,
                "selection_group": selection_group,
                "historical_answer": historical_rows[index].get("en_answer"),
                "corrected_answer": corrected_rows[index].get("en_answer"),
                "question_changed_in_corrected_snapshot": (
                    historical_rows[index].get("en_question") != corrected_rows[index].get("en_question")
                ),
            }
        )

    write_jsonl(output_dir / "source" / "evidence-source-manifest.jsonl", source_manifest)
    smoke_ids = {mappings[changed_indices[0]]["row_id"], mappings[control_indices[0]]["row_id"]}
    smoke_rows = [{**row, "split": "smoke"} for row in source_manifest if row["row_id"] in smoke_ids]
    write_jsonl(output_dir / "source" / "smoke-source-manifest.jsonl", smoke_rows)
    write_jsonl(output_dir / "hidden" / "answer-key.jsonl", hidden_answers)
    write_jsonl(output_dir / "provenance" / "row-mapping.jsonl", mappings)
    write_json(
        output_dir / "provenance" / "pilot-selection.json",
        {
            "seed": seed,
            "selection_algorithm": "all answer changes plus SHA256(seed:row_id)-ranked unchanged rows",
            "answer_changed_row_ids": [mappings[index]["row_id"] for index in changed_indices],
            "unchanged_control_row_ids": [mappings[index]["row_id"] for index in control_indices],
            "smoke_row_ids": [row["row_id"] for row in smoke_rows],
            "smoke_excluded_from_evidence": True,
        },
    )
    provenance = {
        "schema_version": "nl4opt_benchmark_integrity_provenance_v1",
        "official": {
            "path": str(official_path.resolve()),
            "sha256": sha256_file(official_path),
            "git_commit": official_commit,
            "repository": "https://github.com/nl4opt/nl4opt-competition",
        },
        "historical": {
            "path": str(historical_path.resolve()),
            "sha256": sha256_file(historical_path),
        },
        "corrected": {
            "path": str(corrected_path.resolve()),
            "sha256": sha256_file(corrected_path),
            "git_commit": corrected_commit,
            "repository": "https://github.com/Cardinal-Operations/SIRL",
        },
        "counts": {
            "official_targets": len(official_targets),
            "historical_rows": len(historical_rows),
            "answer_changed": len(changed_indices),
            "unchanged_controls": len(control_indices),
            "evidence_rows": len(source_manifest),
            "smoke_sessions": len(smoke_rows),
        },
    }
    write_json(output_dir / "provenance" / "provenance.json", provenance)
    return provenance


def solve_pilot_targets(campaign_dir: Path) -> list[dict[str, Any]]:
    manifest_path = campaign_dir / "source" / "evidence-source-manifest.jsonl"
    rows: list[dict[str, Any]] = []
    for source_row in read_jsonl(manifest_path):
        row_id = str(source_row["row_id"])
        target_path = campaign_dir / "source" / "formal-targets" / f"{row_id}.json"
        target = json.loads(target_path.read_text(encoding="utf-8"))
        payload = target["official_target"]
        rows.append(
            {
                "row_id": row_id,
                "split": source_row["split"],
                "source_id": target["source_id"],
                "formal_target_sha256": sha256_file(target_path),
                "continuous": solve_target(payload, domain="continuous"),
                "integer": solve_target(payload, domain="integer"),
            }
        )
    write_jsonl(campaign_dir / "deterministic" / "formal-target-solver-results.jsonl", rows)
    return rows


def result_matches_answer(result: dict[str, Any], answer: Any, *, tolerance: float = 1e-6) -> bool:
    answer_kind, answer_number = _canonical_answer(answer)
    status = result.get("status")
    if answer_kind == "no_best_solution":
        return status in {"infeasible", "unbounded", "infeasible_or_unbounded"}
    if answer_kind != "numeric" or status != "optimal" or answer_number is None:
        return False
    objective = result.get("objective")
    return isinstance(objective, (int, float)) and math.isclose(
        float(objective), answer_number, rel_tol=tolerance, abs_tol=tolerance
    )


def compare_formal_target_results(campaign_dir: Path) -> list[dict[str, Any]]:
    hidden = {row["row_id"]: row for row in read_jsonl(campaign_dir / "hidden" / "answer-key.jsonl")}
    solver_rows = read_jsonl(campaign_dir / "deterministic" / "formal-target-solver-results.jsonl")
    comparison: list[dict[str, Any]] = []
    for row in solver_rows:
        answer_row = hidden[row["row_id"]]
        historical = answer_row["historical_answer"]
        corrected = answer_row["corrected_answer"]
        continuous = row["continuous"]
        integer = row["integer"]
        historical_matches = {
            "continuous": result_matches_answer(continuous, historical),
            "integer": result_matches_answer(integer, historical),
        }
        corrected_matches = {
            "continuous": result_matches_answer(continuous, corrected),
            "integer": result_matches_answer(integer, corrected),
        }
        comparison.append(
            {
                "row_id": row["row_id"],
                "split": row["split"],
                "selection_group": answer_row["selection_group"],
                "historical_answer": historical,
                "corrected_answer": corrected,
                "continuous_status": continuous.get("status"),
                "continuous_objective": continuous.get("objective"),
                "integer_status": integer.get("status"),
                "integer_objective": integer.get("objective"),
                "historical_matches_continuous": historical_matches["continuous"],
                "historical_matches_integer": historical_matches["integer"],
                "corrected_matches_continuous": corrected_matches["continuous"],
                "corrected_matches_integer": corrected_matches["integer"],
                "formal_target_recovers_correction": (
                    answer_row["selection_group"] == "answer_changed"
                    and any(corrected_matches.values())
                    and not any(historical_matches.values())
                ),
                "domain_ambiguous": (
                    continuous.get("status") != integer.get("status")
                    or not answers_equal(continuous.get("objective"), integer.get("objective"))
                ),
            }
        )
    write_jsonl(campaign_dir / "deterministic" / "formal-target-answer-comparison.jsonl", comparison)
    return comparison


def _selected_domains(audit: dict[str, Any]) -> tuple[str, ...]:
    chosen = audit.get("chosen_domain")
    if chosen == "continuous":
        return ("continuous",)
    if chosen == "integer":
        return ("integer",)
    if chosen == "both":
        return ("continuous", "integer")
    return ()


def compare_model_run(*, campaign_dir: Path, run_dir: Path, role: str) -> list[dict[str, Any]]:
    hidden = {row["row_id"]: row for row in read_jsonl(campaign_dir / "hidden" / "answer-key.jsonl")}
    formal = {
        row["row_id"]: row
        for row in read_jsonl(campaign_dir / "deterministic" / "formal-target-answer-comparison.jsonl")
    }
    source_rows = read_jsonl(campaign_dir / "source" / "evidence-source-manifest.jsonl")
    comparison: list[dict[str, Any]] = []
    for source_row in source_rows:
        row_id = source_row["row_id"]
        workspace = run_dir / "rows" / row_id
        manifest_path = workspace / "run-manifest.json"
        answer_row = hidden[row_id]
        result: dict[str, Any] = {
            "row_id": row_id,
            "selection_group": answer_row["selection_group"],
            "role": role,
            "terminal_status": "not_run",
            "historical_answer": answer_row["historical_answer"],
            "corrected_answer": answer_row["corrected_answer"],
            "chosen_domain": "unresolved",
            "source_status": "unresolved",
            "mechanisms": [],
            "material_ambiguities": [],
            "continuous_status": None,
            "continuous_objective": None,
            "integer_status": None,
            "integer_objective": None,
            "matches_historical": False,
            "matches_corrected": False,
            "supported_discrepancy": False,
            "model_clean": False,
            "terra_clean": False,
            "unsupported_control_escalation": False,
            "formal_target_recovers_correction": formal[row_id]["formal_target_recovers_correction"],
            "proof_ref": str(manifest_path),
        }
        if not manifest_path.is_file():
            comparison.append(result)
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        result["terminal_status"] = manifest.get("terminal_status", "unknown")
        if result["terminal_status"] != "success":
            comparison.append(result)
            continue
        report_path = workspace / "parent_solver_report.json"
        audit_path = workspace / "audit.json"
        if not report_path.is_file() or not audit_path.is_file():
            result["terminal_status"] = "post_session_artifact_missing"
            comparison.append(result)
            continue
        report = json.loads(report_path.read_text(encoding="utf-8"))
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        result.update(
            {
                "chosen_domain": audit.get("chosen_domain", "unresolved"),
                "source_status": audit.get("source_status", "unresolved"),
                "mechanisms": audit.get("mechanisms", []),
                "material_ambiguities": audit.get("material_ambiguities", []),
                "continuous_status": report.get("continuous", {}).get("status"),
                "continuous_objective": report.get("continuous", {}).get("objective"),
                "integer_status": report.get("integer", {}).get("status"),
                "integer_objective": report.get("integer", {}).get("objective"),
            }
        )
        domains = _selected_domains(audit)
        historical_matches = [
            result_matches_answer(report.get(domain, {}), answer_row["historical_answer"]) for domain in domains
        ]
        corrected_matches = [
            result_matches_answer(report.get(domain, {}), answer_row["corrected_answer"]) for domain in domains
        ]
        result["matches_historical"] = any(historical_matches)
        result["matches_corrected"] = any(corrected_matches)
        result["supported_discrepancy"] = bool(
            answer_row["selection_group"] == "answer_changed"
            and result["matches_corrected"]
            and not result["matches_historical"]
        )
        result["model_clean"] = bool(
            answer_row["selection_group"] == "unchanged_control"
            and result["matches_historical"]
            and result["source_status"] != "inconsistent"
        )
        result["terra_clean"] = role == "terra" and result["model_clean"]
        escalated = bool(
            result["source_status"] != "well_posed"
            or result["material_ambiguities"]
            or any(value in {"contradicted", "unsupported"} for value in _anchor_support_labels(workspace))
        )
        continuous = report.get("continuous", {})
        integer = report.get("integer", {})
        domains_disagree = (
            continuous.get("status") != integer.get("status")
            or not answers_equal(continuous.get("objective"), integer.get("objective"))
        )
        solver_support = not result["matches_historical"] or domains_disagree
        result["unsupported_control_escalation"] = bool(
            answer_row["selection_group"] == "unchanged_control" and escalated and not solver_support
        )
        comparison.append(result)
    output_path = campaign_dir / "comparisons" / f"{role}-answer-comparison.jsonl"
    write_jsonl(output_path, comparison)
    return comparison


def _anchor_support_labels(workspace: Path) -> list[str]:
    path = workspace / "source_anchors.csv"
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [str(row.get("support_label", "")) for row in csv.DictReader(handle)]


def build_owner_review_packet(*, campaign_dir: Path) -> dict[str, Any]:
    terra = {
        row["row_id"]: row
        for row in read_jsonl(campaign_dir / "comparisons" / "terra-answer-comparison.jsonl")
    }
    sol = {
        row["row_id"]: row
        for row in read_jsonl(campaign_dir / "comparisons" / "sol-answer-comparison.jsonl")
    }
    selected = read_jsonl(campaign_dir / "source" / "sol-source-manifest.jsonl")
    if len(selected) > 12:
        raise NL4OPTError(f"owner packet exceeds 12-row cap: {len(selected)}")
    rows: list[dict[str, Any]] = []
    for source_row in selected:
        row_id = source_row["row_id"]
        terra_row = terra[row_id]
        sol_row = sol[row_id]
        statement_path = campaign_dir / source_row["statement_path"]
        rows.append(
            {
                "row_id": row_id,
                "selection_group": terra_row["selection_group"],
                "statement_path": str(statement_path),
                "historical_answer": terra_row["historical_answer"],
                "corrected_answer": terra_row["corrected_answer"],
                "terra_source_status": terra_row["source_status"],
                "terra_domain": terra_row["chosen_domain"],
                "terra_continuous_objective": terra_row["continuous_objective"],
                "terra_integer_objective": terra_row["integer_objective"],
                "terra_mechanisms": ";".join(terra_row["mechanisms"]),
                "sol_source_status": sol_row["source_status"],
                "sol_domain": sol_row["chosen_domain"],
                "sol_continuous_objective": sol_row["continuous_objective"],
                "sol_integer_objective": sol_row["integer_objective"],
                "sol_mechanisms": ";".join(sol_row["mechanisms"]),
                "model_agreement": (
                    terra_row["chosen_domain"] == sol_row["chosen_domain"]
                    and terra_row["continuous_status"] == sol_row["continuous_status"]
                    and answers_equal(terra_row["continuous_objective"], sol_row["continuous_objective"])
                    and terra_row["integer_status"] == sol_row["integer_status"]
                    and answers_equal(terra_row["integer_objective"], sol_row["integer_objective"])
                ),
                "owner_decision": "",
                "owner_material": "",
                "owner_mechanism": "",
                "owner_notes": "",
            }
        )
    fields = list(rows[0]) if rows else ["row_id"]
    csv_path = campaign_dir / "owner-review" / "owner-review-packet.csv"
    write_csv(csv_path, rows, fields)
    markdown_lines = [
        "# Owner Review Packet",
        "",
        "Review all rows. Fill the four `owner_*` columns in the CSV. This is the only human gate.",
        "",
    ]
    for row in rows:
        statement = Path(row["statement_path"]).read_text(encoding="utf-8").strip()
        markdown_lines.extend(
            [
                f"## {row['row_id']}",
                "",
                statement,
                "",
                f"- Historical answer: `{row['historical_answer']}`",
                f"- Corrected answer: `{row['corrected_answer']}`",
                f"- Terra: domain `{row['terra_domain']}`, continuous `{row['terra_continuous_objective']}`, integer `{row['terra_integer_objective']}`",
                f"- Sol: domain `{row['sol_domain']}`, continuous `{row['sol_continuous_objective']}`, integer `{row['sol_integer_objective']}`",
                f"- Independent-model agreement: `{row['model_agreement']}`",
                "- Owner decision: pending",
                "",
            ]
        )
    markdown_path = campaign_dir / "owner-review" / "OWNER_REVIEW.md"
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n".join(markdown_lines).rstrip() + "\n", encoding="utf-8")
    summary = {"rows": len(rows), "csv": str(csv_path), "markdown": str(markdown_path), "status": "owner_review_pending"}
    write_json(campaign_dir / "owner-review" / "owner-review-status.json", summary)
    return summary


def validate_source_manifest(manifest_path: Path, campaign_dir: Path) -> dict[str, Any]:
    allowed_fields = {"row_id", "split", "statement_path", "source_sha256"}
    errors: list[str] = []
    rows = read_jsonl(manifest_path)
    seen: set[str] = set()
    for line_number, row in enumerate(rows, start=1):
        extra = set(row) - allowed_fields
        missing = allowed_fields - set(row)
        if extra:
            errors.append(f"line {line_number}: forbidden/extra fields {sorted(extra)}")
        if missing:
            errors.append(f"line {line_number}: missing fields {sorted(missing)}")
            continue
        row_id = str(row["row_id"])
        if row_id in seen:
            errors.append(f"line {line_number}: duplicate row_id {row_id}")
        seen.add(row_id)
        statement_path = (campaign_dir / str(row["statement_path"])).resolve()
        source_root = (campaign_dir / "source").resolve()
        if source_root not in statement_path.parents:
            errors.append(f"line {line_number}: statement path escapes source root")
        elif not statement_path.is_file():
            errors.append(f"line {line_number}: statement missing: {statement_path}")
        elif sha256_file(statement_path) != row["source_sha256"]:
            errors.append(f"line {line_number}: statement hash mismatch")
    return {
        "status": "valid" if not errors else "invalid",
        "row_count": len(rows),
        "manifest_path": str(manifest_path.resolve()),
        "errors": errors,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
