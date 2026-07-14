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

from or_ci.benchmark_answers import (
    AnswerPolicy,
    NL4OPT_ANSWER_POLICY,
    answer_encoding,
    answer_relation,
    answers_equal,
    canonical_solver_status,
    result_matches_answer,
    semantic_answer,
)


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

OWNER_DECISION_OPTIONS = (
    "sirl_supported",
    "dataset_supported",
    "both_valid",
    "neither_supported",
    "unresolved",
)
OWNER_DECISION_VALUES = set(OWNER_DECISION_OPTIONS)
OWNER_MATERIAL_OPTIONS = ("yes", "no", "uncertain")
OWNER_MATERIAL_VALUES = set(OWNER_MATERIAL_OPTIONS)
OWNER_MECHANISM_OPTIONS = (
    "domain_or_integrality_ambiguity",
    "infeasible_unbounded_status_encoding",
    "strict_inequality_semantics",
    "constraint_or_ratio_interpretation",
    "reference_value_or_arithmetic_error",
    "equivalent_answer_or_tolerance",
    "none",
)
OWNER_MECHANISM_VALUES = set(OWNER_MECHANISM_OPTIONS)
OWNER_FIELDS = (
    "owner_decision",
    "owner_material",
    "owner_mechanism",
)
CONFIRMED_FAULT_DECISIONS = {"sirl_supported", "neither_supported"}


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

    raw_changed_indices = [
        index
        for index, (historical, corrected) in enumerate(zip(historical_rows, corrected_rows, strict=True))
        if str(historical.get("en_answer")) != str(corrected.get("en_answer"))
    ]
    changed_indices = [
        index
        for index, (historical, corrected) in enumerate(zip(historical_rows, corrected_rows, strict=True))
        if not answers_equal(historical.get("en_answer"), corrected.get("en_answer"))
    ]
    encoding_only_indices = [
        index
        for index in raw_changed_indices
        if answers_equal(
            historical_rows[index].get("en_answer"),
            corrected_rows[index].get("en_answer"),
        )
    ]
    if len(changed_indices) != expected_answer_changes:
        raise NL4OPTError(
            f"expected {expected_answer_changes} answer changes, observed {len(changed_indices)}"
        )
    unchanged_candidates = [
        index
        for index, (historical, corrected) in enumerate(zip(historical_rows, corrected_rows, strict=True))
        if historical.get("en_question") == corrected.get("en_question")
        and answers_equal(historical.get("en_answer"), corrected.get("en_answer"))
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
                "answer_relation": answer_relation(
                    historical_rows[index].get("en_answer"),
                    corrected_rows[index].get("en_answer"),
                ),
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
            "selection_algorithm": "all semantic answer changes plus SHA256(seed:row_id)-ranked semantically unchanged rows",
            "answer_changed_row_ids": [mappings[index]["row_id"] for index in changed_indices],
            "encoding_only_row_ids": [mappings[index]["row_id"] for index in encoding_only_indices],
            "unchanged_control_row_ids": [mappings[index]["row_id"] for index in control_indices],
            "smoke_row_ids": [row["row_id"] for row in smoke_rows],
            "smoke_excluded_from_evidence": True,
        },
    )
    provenance = {
        "schema_version": "nl4opt_benchmark_integrity_provenance_v2",
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
            "raw_answer_changed": len(raw_changed_indices),
            "encoding_only_changed": len(encoding_only_indices),
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


def compare_formal_target_results(campaign_dir: Path) -> list[dict[str, Any]]:
    hidden = {row["row_id"]: row for row in read_jsonl(campaign_dir / "hidden" / "answer-key.jsonl")}
    solver_rows = read_jsonl(campaign_dir / "deterministic" / "formal-target-solver-results.jsonl")
    comparison: list[dict[str, Any]] = []
    for row in solver_rows:
        answer_row = hidden[row["row_id"]]
        historical = answer_row["historical_answer"]
        corrected = answer_row["corrected_answer"]
        relation = answer_relation(historical, corrected)
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
                "answer_relation": relation,
                "continuous_status": continuous.get("status"),
                "continuous_objective": continuous.get("objective"),
                "integer_status": integer.get("status"),
                "integer_objective": integer.get("objective"),
                "historical_matches_continuous": historical_matches["continuous"],
                "historical_matches_integer": historical_matches["integer"],
                "corrected_matches_continuous": corrected_matches["continuous"],
                "corrected_matches_integer": corrected_matches["integer"],
                "formal_target_recovers_correction": (
                    relation == "semantic_difference"
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


def _campaign_answer_policy(campaign_dir: Path) -> AnswerPolicy:
    provenance_path = campaign_dir / "provenance" / "provenance.json"
    if not provenance_path.is_file():
        return NL4OPT_ANSWER_POLICY
    payload = json.loads(provenance_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("answer_policy"), dict):
        return NL4OPT_ANSWER_POLICY
    try:
        return AnswerPolicy.from_mapping(payload["answer_policy"])
    except (TypeError, ValueError) as exc:
        raise NL4OPTError(f"invalid campaign answer policy: {exc}") from exc


def _result_status_class(result: dict[str, Any]) -> str:
    status = canonical_solver_status(result.get("status", ""))
    if status == "optimal":
        return "optimal"
    if status in {
        "infeasible",
        "unbounded",
        "infeasible_or_unbounded",
        "strict_inequality_infimum_not_attained",
        "no_attained_minimum_strict_continuous",
        "no_attained_maximum_strict_continuous",
    }:
        return "no_best_solution"
    return status or "missing"


def _domain_results_agree(
    left: dict[str, Any],
    right: dict[str, Any],
    *,
    policy: AnswerPolicy,
) -> bool:
    left_class = _result_status_class(left)
    right_class = _result_status_class(right)
    if left_class != right_class or left_class == "missing":
        return False
    if left_class != "optimal":
        return True
    left_objective = left.get("objective")
    right_objective = right.get("objective")
    if not isinstance(left_objective, (int, float)) or not isinstance(
        right_objective, (int, float)
    ):
        return False
    return answers_equal(left_objective, right_objective, policy=policy)


def _selected_domain_matches(
    report: dict[str, Any],
    audit: dict[str, Any],
    answer: Any,
    *,
    policy: AnswerPolicy,
) -> tuple[bool, bool]:
    domains = _selected_domains(audit)
    if not domains:
        return False, True
    selected = [report.get(domain, {}) for domain in domains]
    if any(not isinstance(item, dict) or _result_status_class(item) == "missing" for item in selected):
        return False, True
    if len(selected) == 2 and not _domain_results_agree(selected[0], selected[1], policy=policy):
        return False, True
    return all(result_matches_answer(item, answer, policy=policy) for item in selected), False


def compare_model_run(*, campaign_dir: Path, run_dir: Path, role: str) -> list[dict[str, Any]]:
    policy = _campaign_answer_policy(campaign_dir)
    hidden = {row["row_id"]: row for row in read_jsonl(campaign_dir / "hidden" / "answer-key.jsonl")}
    formal_path = campaign_dir / "deterministic" / "formal-target-answer-comparison.jsonl"
    formal = {row["row_id"]: row for row in read_jsonl(formal_path)} if formal_path.is_file() else {}
    source_manifest = campaign_dir / "source" / "evidence-source-manifest.jsonl"
    sol_manifest = campaign_dir / "source" / "sol-source-manifest.jsonl"
    if role == "sol" and sol_manifest.is_file():
        source_manifest = sol_manifest
    source_rows = read_jsonl(source_manifest)
    comparison: list[dict[str, Any]] = []
    for source_row in source_rows:
        row_id = source_row["row_id"]
        workspace = run_dir / "rows" / row_id
        manifest_path = workspace / "run-manifest.json"
        answer_row = hidden[row_id]
        relation = answer_relation(
            answer_row["historical_answer"],
            answer_row["corrected_answer"],
            policy=policy,
        )
        result: dict[str, Any] = {
            "row_id": row_id,
            "selection_group": answer_row["selection_group"],
            "role": role,
            "terminal_status": "not_run",
            "historical_answer": answer_row["historical_answer"],
            "corrected_answer": answer_row["corrected_answer"],
            "answer_relation": relation,
            "chosen_domain": "unresolved",
            "source_selected_domain": "unresolved",
            "domain_ambiguous": True,
            "source_status": "unresolved",
            "mechanisms": [],
            "material_ambiguities": [],
            "continuous_status": None,
            "continuous_objective": None,
            "integer_status": None,
            "integer_objective": None,
            "matches_historical": False,
            "matches_corrected": False,
            "matches_historical_any_domain": False,
            "matches_corrected_any_domain": False,
            "matches_historical_selected_domain": False,
            "matches_corrected_selected_domain": False,
            "correction_reproduced_any_domain": False,
            "correction_discriminated": False,
            "revised_reproduced_selected_domain": False,
            "revised_discriminated_selected_domain": False,
            "unchanged_control_disagreement_selected_domain": False,
            "supported_discrepancy": False,
            "model_clean": False,
            "terra_clean": False,
            "control_escalated": False,
            "solver_support_for_escalation": False,
            "unsupported_control_escalation": False,
            "formal_target_recovers_correction": formal.get(row_id, {}).get(
                "formal_target_recovers_correction"
            ),
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
                "source_selected_domain": audit.get("chosen_domain", "unresolved"),
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
            result_matches_answer(
                report.get(domain, {}), answer_row["historical_answer"], policy=policy
            )
            for domain in domains
        ]
        corrected_matches = [
            result_matches_answer(
                report.get(domain, {}), answer_row["corrected_answer"], policy=policy
            )
            for domain in domains
        ]
        all_domain_historical_matches = [
            result_matches_answer(
                report.get(domain, {}), answer_row["historical_answer"], policy=policy
            )
            for domain in ("continuous", "integer")
        ]
        all_domain_corrected_matches = [
            result_matches_answer(
                report.get(domain, {}), answer_row["corrected_answer"], policy=policy
            )
            for domain in ("continuous", "integer")
        ]
        historical_selected, historical_ambiguous = _selected_domain_matches(
            report,
            audit,
            answer_row["historical_answer"],
            policy=policy,
        )
        corrected_selected, corrected_ambiguous = _selected_domain_matches(
            report,
            audit,
            answer_row["corrected_answer"],
            policy=policy,
        )
        domain_ambiguous = historical_ambiguous or corrected_ambiguous
        result["matches_historical"] = any(historical_matches)
        result["matches_corrected"] = any(corrected_matches)
        result["matches_historical_any_domain"] = any(all_domain_historical_matches)
        result["matches_corrected_any_domain"] = any(all_domain_corrected_matches)
        result["matches_historical_selected_domain"] = historical_selected
        result["matches_corrected_selected_domain"] = corrected_selected
        result["domain_ambiguous"] = domain_ambiguous
        result["correction_reproduced_any_domain"] = bool(
            relation == "semantic_difference" and result["matches_corrected_any_domain"]
        )
        result["correction_discriminated"] = bool(
            relation == "semantic_difference"
            and result["matches_corrected"]
            and not result["matches_historical"]
        )
        result["revised_reproduced_selected_domain"] = bool(
            relation == "semantic_difference" and corrected_selected and not domain_ambiguous
        )
        result["revised_discriminated_selected_domain"] = bool(
            relation == "semantic_difference"
            and corrected_selected
            and not historical_selected
            and not domain_ambiguous
        )
        result["unchanged_control_disagreement_selected_domain"] = bool(
            answer_row["selection_group"] == "unchanged_control"
            and (domain_ambiguous or not historical_selected)
        )
        result["supported_discrepancy"] = bool(
            relation == "semantic_difference"
            and result["matches_corrected_any_domain"]
        )
        result["model_clean"] = bool(
            answer_row["selection_group"] == "unchanged_control"
            and result["matches_historical"]
            and result["source_status"] != "inconsistent"
        )
        result["terra_clean"] = role == "terra" and result["model_clean"]
        escalated = bool(
            result["source_status"] == "inconsistent"
            or result["chosen_domain"] == "unresolved"
            or any(value in {"contradicted", "unsupported"} for value in _anchor_support_labels(workspace))
        )
        continuous = report.get("continuous", {})
        integer = report.get("integer", {})
        domains_disagree = (
            not _domain_results_agree(continuous, integer, policy=policy)
        )
        statuses = [_result_status_class(continuous), _result_status_class(integer)]
        has_status_or_iis_support = any(status != "optimal" for status in statuses) or any(
            domain_result.get("iis_constraints")
            for domain_result in (continuous, integer)
            if isinstance(domain_result, dict)
        )
        solver_support = not result["matches_historical_any_domain"] or domains_disagree or has_status_or_iis_support
        result["control_escalated"] = bool(
            answer_row["selection_group"] == "unchanged_control" and escalated
        )
        result["solver_support_for_escalation"] = solver_support
        result["unsupported_control_escalation"] = bool(
            result["control_escalated"] and not solver_support
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


def serialize_mechanisms(items: Any) -> str:
    if not isinstance(items, list):
        return ""
    return ";".join(
        item if isinstance(item, str) else json.dumps(item, ensure_ascii=False, sort_keys=True)
        for item in items
    )


def solver_reports_agree(left: dict[str, Any], right: dict[str, Any]) -> bool:
    for domain in ("continuous", "integer"):
        left_result = left.get(domain, {})
        right_result = right.get(domain, {})
        if str(left_result.get("status", "")).lower() != str(right_result.get("status", "")).lower():
            return False
        left_objective = left_result.get("objective")
        right_objective = right_result.get("objective")
        if left_objective is None or right_objective is None:
            if left_objective != right_objective:
                return False
        elif not math.isclose(float(left_objective), float(right_objective), rel_tol=1e-6, abs_tol=1e-6):
            return False
    return True


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise NL4OPTError(f"required review artifact is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise NL4OPTError(f"required review artifact must be a JSON object: {path}")
    return payload


def _display_value(value: Any) -> str:
    if value is None or value == "":
        return "not available"
    if isinstance(value, dict):
        if not value:
            return "not available"
        return "; ".join(f"{key}: {_display_value(item)}" for key, item in value.items())
    if isinstance(value, list):
        if not value:
            return "not available"
        return ", ".join(_display_value(item) for item in value)
    return str(value).replace("\n", " ").strip()


def _model_record_label(item: dict[str, Any], fallback: str) -> str:
    labels: list[str] = []
    for key in ("symbol", "id", "name", "domain"):
        value = item.get(key)
        if value not in (None, "") and str(value) not in labels:
            labels.append(str(value))
    return " / ".join(labels) if labels else fallback


def _model_record_lines(
    items: Any,
    *,
    label_prefix: str,
    excluded_keys: set[str],
) -> list[str]:
    if isinstance(items, dict):
        normalized_items = [
            {"domain": key, **value} if isinstance(value, dict) else {"domain": key, "value": value}
            for key, value in items.items()
        ]
    elif isinstance(items, list):
        normalized_items = [item for item in items if isinstance(item, dict)]
    else:
        normalized_items = []
    lines: list[str] = []
    for index, item in enumerate(normalized_items, start=1):
        label = _model_record_label(item, f"{label_prefix}_{index}")
        lines.append(f"- {label}")
        for key, value in item.items():
            if key in excluded_keys or key.endswith(("source_quote", "source_quotes")):
                continue
            lines.append(f"  {key}: {_display_value(value)}")
    return lines or ["- not recorded"]


def _generated_model_text(model: dict[str, Any]) -> str:
    objective = model.get("objective")
    objective_lines = (
        _model_record_lines(
            [objective],
            label_prefix="objective",
            excluded_keys={"id", "name", "symbol", "domain"},
        )
        if isinstance(objective, dict)
        else ["- not recorded"]
    )
    sections = [
        "Variables:",
        *_model_record_lines(
            model.get("variables"),
            label_prefix="variable",
            excluded_keys={"id", "name", "symbol", "domain"},
        ),
        "",
        "Objective:",
        *objective_lines,
        "",
        "Constraints:",
        *_model_record_lines(
            model.get("constraints"),
            label_prefix="constraint",
            excluded_keys={"id", "name", "symbol", "domain"},
        ),
        "",
        "Assumptions:",
        *_model_record_lines(
            model.get("assumptions"),
            label_prefix="assumption",
            excluded_keys={"id", "name", "symbol", "domain"},
        ),
        "",
        "Domain evidence:",
        *_model_record_lines(
            model.get("domain_evidence"),
            label_prefix="domain",
            excluded_keys={"id", "name", "symbol", "domain"},
        ),
    ]
    return "\n".join(sections)


def _markdown_cell(value: Any) -> str:
    return _display_value(value).replace("|", "\\|")


def _solver_answer_row(label: str, domain: str, report: dict[str, Any]) -> str:
    result = report.get(domain, {})
    if not isinstance(result, dict):
        result = {}
    return (
        f"| {label} | {domain} | {_markdown_cell(result.get('status'))} | "
        f"{_markdown_cell(result.get('objective'))} | {_markdown_cell(result.get('variables'))} |"
    )


def _answer_role(base: str, encoding: str) -> str:
    if encoding.startswith("sentinel_minus_"):
        marker = "-" + encoding.removeprefix("sentinel_minus_")
        return f"{base}; {marker} is a no-best-solution sentinel, not an objective value"
    return base


def _markdown_owner_values(markdown_path: Path) -> dict[str, dict[str, str]]:
    if not markdown_path.is_file():
        return {}
    values: dict[str, dict[str, str]] = {}
    current_row: str | None = None
    current_field: str | None = None
    for line in markdown_path.read_text(encoding="utf-8").splitlines():
        row_match = re.fullmatch(r"## ([a-z0-9][a-z0-9_-]*-row-\d+)", line)
        if row_match:
            current_row = row_match.group(1)
            current_field = None
            continue
        field_match = re.fullmatch(r"#### (owner_[a-z_]+)", line)
        if field_match and current_row and field_match.group(1) in OWNER_FIELDS:
            current_field = field_match.group(1)
            values.setdefault(current_row, {})[current_field] = ""
            continue
        if line.startswith("#"):
            current_field = None
            continue
        option_match = re.fullmatch(r"- \[([ xX])\] ([A-Za-z0-9_:-]+)", line)
        if not option_match or not current_row or not current_field:
            continue
        if option_match.group(1).lower() != "x":
            continue
        selected = option_match.group(2)
        previous = values[current_row][current_field]
        if previous:
            raise NL4OPTError(
                f"{current_row}: multiple Markdown selections for {current_field}: "
                f"{previous!r}, {selected!r}"
            )
        values[current_row][current_field] = selected
    return values


def _owner_option_lines(options: tuple[str, ...], selected: str) -> list[str]:
    return [f"- [{'x' if option == selected else ' '}] {option}" for option in options]


def _existing_owner_values(csv_path: Path, markdown_path: Path) -> dict[str, dict[str, str]]:
    values: dict[str, dict[str, str]] = {}
    if csv_path.is_file():
        with csv_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames and "row_id" in reader.fieldnames:
                for row in reader:
                    row_id = str(row.get("row_id", "")).strip()
                    if not row_id:
                        continue
                    if row_id in values:
                        raise NL4OPTError(f"duplicate owner-review row: {row_id}")
                    values[row_id] = {
                        field: str(row.get(field, "") or "").strip()
                        for field in OWNER_FIELDS
                    }
    for row_id, markdown_values in _markdown_owner_values(markdown_path).items():
        values.setdefault(row_id, {field: "" for field in OWNER_FIELDS}).update(markdown_values)
    return values


def _owner_review_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    missing_fields: list[str] = []
    errors: list[str] = []
    completed_rows = 0
    confirmed_rows: list[str] = []
    confirmed_mechanisms: set[str] = set()
    for index, row in enumerate(rows, start=2):
        row_id = str(row.get("row_id") or f"line-{index}")
        values = {field: str(row.get(field, "") or "").strip() for field in OWNER_FIELDS}
        row_missing = [field for field, value in values.items() if not value]
        missing_fields.extend(f"{row_id}:{field}" for field in row_missing)
        if row_missing:
            continue
        completed_rows += 1
        decision = values["owner_decision"]
        material = values["owner_material"]
        mechanism = values["owner_mechanism"]
        if decision not in OWNER_DECISION_VALUES:
            errors.append(f"{row_id}: invalid owner_decision {decision!r}")
        if material not in OWNER_MATERIAL_VALUES:
            errors.append(f"{row_id}: invalid owner_material {material!r}")
        mechanism_valid = mechanism in OWNER_MECHANISM_VALUES
        if not mechanism_valid:
            errors.append(f"{row_id}: invalid owner_mechanism {mechanism!r}")
        if material == "yes" and mechanism == "none":
            errors.append(f"{row_id}: owner_material yes requires a non-none mechanism")
        if (
            decision in CONFIRMED_FAULT_DECISIONS
            and material == "yes"
            and mechanism_valid
            and mechanism != "none"
        ):
            confirmed_rows.append(row_id)
            confirmed_mechanisms.add(mechanism)
    if errors:
        status = "invalid"
        gate_status = "pending"
    elif missing_fields:
        status = "pending"
        gate_status = "pending"
    else:
        status = "valid_complete"
        gate_status = (
            "pass"
            if len(confirmed_rows) >= 3 and len(confirmed_mechanisms) >= 2
            else "fail"
        )
    return {
        "schema_version": "owner_review_status_v3",
        "status": status,
        "gate_status": gate_status,
        "rows": len(rows),
        "completed_rows": completed_rows,
        "pending_rows": len(rows) - completed_rows,
        "missing_fields": missing_fields,
        "errors": errors,
        "confirmed_material_answer_fault_rows": confirmed_rows,
        "confirmed_material_answer_fault_count": len(confirmed_rows),
        "confirmed_mechanisms": sorted(confirmed_mechanisms),
        "confirmed_mechanism_count": len(confirmed_mechanisms),
    }


def build_owner_review_packet(*, campaign_dir: Path) -> dict[str, Any]:
    policy = _campaign_answer_policy(campaign_dir)
    provenance_path = campaign_dir / "provenance" / "provenance.json"
    provenance = (
        json.loads(provenance_path.read_text(encoding="utf-8"))
        if provenance_path.is_file()
        else {}
    )
    corpus = str(provenance.get("corpus", "NL4OPT")) if isinstance(provenance, dict) else "NL4OPT"
    terra = {
        row["row_id"]: row
        for row in read_jsonl(campaign_dir / "comparisons" / "terra-answer-comparison.jsonl")
    }
    sol = {
        row["row_id"]: row
        for row in read_jsonl(campaign_dir / "comparisons" / "sol-answer-comparison.jsonl")
    }
    selected_manifest = read_jsonl(campaign_dir / "source" / "sol-source-manifest.jsonl")
    if len(selected_manifest) > 12:
        raise NL4OPTError(f"owner packet exceeds 12-row cap: {len(selected_manifest)}")
    selected: list[dict[str, Any]] = []
    excluded_encoding_rows: list[str] = []
    for source_row in selected_manifest:
        row_id = source_row["row_id"]
        if row_id not in terra or row_id not in sol:
            raise NL4OPTError(f"owner row lacks Terra or Sol comparison: {row_id}")
        relation = terra[row_id].get("answer_relation") or answer_relation(
            terra[row_id]["historical_answer"],
            terra[row_id]["corrected_answer"],
            policy=policy,
        )
        if relation == "encoding_equivalent":
            excluded_encoding_rows.append(row_id)
            continue
        selected.append(source_row)
    csv_path = campaign_dir / "owner-review" / "owner-review-packet.csv"
    markdown_path = campaign_dir / "owner-review" / "OWNER_REVIEW.md"
    existing_owner_values = _existing_owner_values(csv_path, markdown_path)
    rows: list[dict[str, Any]] = []
    render_material: dict[
        str,
        tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]],
    ] = {}
    for source_row in selected:
        row_id = source_row["row_id"]
        if row_id not in terra or row_id not in sol:
            raise NL4OPTError(f"owner row lacks Terra or Sol comparison: {row_id}")
        terra_row = terra[row_id]
        sol_row = sol[row_id]
        statement_path = campaign_dir / source_row["statement_path"]
        terra_workspace = campaign_dir / "runs" / "terra-evidence" / "rows" / row_id
        sol_workspace = campaign_dir / "runs" / "sol-adjudication" / "rows" / row_id
        terra_report = _read_json_object(terra_workspace / "parent_solver_report.json")
        sol_report = _read_json_object(sol_workspace / "parent_solver_report.json")
        terra_model = _read_json_object(terra_workspace / "problem.json")
        sol_model = _read_json_object(sol_workspace / "problem.json")
        render_material[row_id] = (terra_model, terra_report, sol_model, sol_report)
        domain_assessment_agreement = terra_row["chosen_domain"] == sol_row["chosen_domain"]
        dataset_answer_raw = terra_row["historical_answer"]
        sirl_revised_answer_raw = terra_row["corrected_answer"]
        relation = terra_row.get("answer_relation") or answer_relation(
            dataset_answer_raw,
            sirl_revised_answer_raw,
            policy=policy,
        )
        owner_values = existing_owner_values.get(row_id, {})
        rows.append(
            {
                "row_id": row_id,
                "selection_group": terra_row["selection_group"],
                "answer_relation": relation,
                "statement_path": str(statement_path),
                "dataset_answer": semantic_answer(dataset_answer_raw, policy=policy),
                "dataset_answer_raw": dataset_answer_raw,
                "dataset_answer_encoding": answer_encoding(dataset_answer_raw, policy=policy),
                "sirl_revised_answer": semantic_answer(sirl_revised_answer_raw, policy=policy),
                "sirl_revised_answer_raw": sirl_revised_answer_raw,
                "sirl_revised_answer_encoding": answer_encoding(
                    sirl_revised_answer_raw, policy=policy
                ),
                "terra_model_path": str(terra_workspace / "problem.json"),
                "terra_source_status": terra_row["source_status"],
                "terra_chosen_domain": terra_row["chosen_domain"],
                "terra_generated_continuous_status": terra_report.get("continuous", {}).get("status"),
                "terra_generated_continuous_answer": terra_report.get("continuous", {}).get("objective"),
                "terra_generated_integer_status": terra_report.get("integer", {}).get("status"),
                "terra_generated_integer_answer": terra_report.get("integer", {}).get("objective"),
                "terra_mechanisms": serialize_mechanisms(terra_row["mechanisms"]),
                "sol_model_path": str(sol_workspace / "problem.json"),
                "sol_source_status": sol_row["source_status"],
                "sol_chosen_domain": sol_row["chosen_domain"],
                "sol_generated_continuous_status": sol_report.get("continuous", {}).get("status"),
                "sol_generated_continuous_answer": sol_report.get("continuous", {}).get("objective"),
                "sol_generated_integer_status": sol_report.get("integer", {}).get("status"),
                "sol_generated_integer_answer": sol_report.get("integer", {}).get("objective"),
                "sol_mechanisms": serialize_mechanisms(sol_row["mechanisms"]),
                "solver_result_agreement": solver_reports_agree(terra_report, sol_report),
                "domain_assessment_agreement": domain_assessment_agreement,
                "model_agreement": domain_assessment_agreement and solver_reports_agree(terra_report, sol_report),
                **{field: owner_values.get(field, "") for field in OWNER_FIELDS},
            }
        )
    fields = list(rows[0]) if rows else ["row_id", *OWNER_FIELDS]
    write_csv(csv_path, rows, fields)
    markdown_lines = [
        "# Owner Review Packet",
        "",
        "This packet separates three answer roles. The dataset answer is the older local",
        f"{corpus} answer. The SIRL-revised answer is an external published revision, not",
        "ground truth. The workflow-generated role contains two independent generators,",
        "Terra and Sol; each model is replayed in continuous and integer domains.",
        "The frozen status markers "
        + ", ".join(str(value) for value in policy.status_sentinels)
        + " mean No Best Solution; they are not numeric objectives.",
        "A marker alone does not distinguish infeasible, unbounded,",
        "or an unattained optimum, so use the generated solver statuses for that detail.",
        "Rows where dataset and SIRL values differ only by encoding are excluded",
        "from owner review.",
        "",
        "Review every row, including controls. In each row, mark exactly one",
        "checkbox in each of the three owner selection lists.",
        "",
        "## Required Owner Values",
        "",
        "- owner_decision: sirl_supported, dataset_supported, both_valid, neither_supported, or unresolved",
        "- owner_material: yes, no, or uncertain",
        "- owner_mechanism: one listed mechanism or none",
        "",
        "Allowed mechanisms: " + ", ".join(sorted(OWNER_MECHANISM_VALUES - {"none"})) + ", none.",
        "",
        "A confirmed material answer fault requires owner_decision sirl_supported or",
        "neither_supported, owner_material yes, and a non-none mechanism.",
        "The campaign gate requires at least three such rows across at least two mechanisms.",
        "Completing this owner gate does not repair or replace an invalid recovery gate.",
        "",
    ]
    for row in rows:
        row_id = row["row_id"]
        statement = Path(row["statement_path"]).read_text(encoding="utf-8").strip()
        terra_model, terra_report, sol_model, sol_report = render_material[row_id]
        markdown_lines.extend(
            [
                f"## {row_id}",
                "",
                "### Question",
                "",
                statement,
                "",
                f"- Frozen selection group: {_display_value(row['selection_group'])}",
                f"- Repaired answer relation: {_display_value(row['answer_relation'])}",
                "",
                "### Answer Sources",
                "",
                "| Source | Interpreted answer | Raw stored value | Role |",
                "|---|---:|---:|---|",
                f"| Original dataset snapshot | {_markdown_cell(row['dataset_answer'])} | {_markdown_cell(row['dataset_answer_raw'])} | {_answer_role('Answer being audited', row['dataset_answer_encoding'])} |",
                f"| SIRL revised snapshot | {_markdown_cell(row['sirl_revised_answer'])} | {_markdown_cell(row['sirl_revised_answer_raw'])} | {_answer_role('External revision; not ground truth', row['sirl_revised_answer_encoding'])} |",
                "",
                "### Workflow-Generated Answers",
                "",
                "| Generator | Domain | Status | Objective answer | Variable values |",
                "|---|---|---|---:|---|",
                _solver_answer_row("Terra", "continuous", terra_report),
                _solver_answer_row("Terra", "integer", terra_report),
                _solver_answer_row("Sol", "continuous", sol_report),
                _solver_answer_row("Sol", "integer", sol_report),
                "",
                f"- Terra source assessment: {_display_value(row['terra_source_status'])}",
                f"- Terra chosen domain: {_display_value(row['terra_chosen_domain'])}",
                f"- Sol source assessment: {_display_value(row['sol_source_status'])}",
                f"- Sol chosen domain: {_display_value(row['sol_chosen_domain'])}",
                f"- Solver-result agreement: {_display_value(row['solver_result_agreement'])}",
                f"- Domain-assessment agreement: {_display_value(row['domain_assessment_agreement'])}",
                "",
                "### Terra-Generated Mathematical Model",
                "",
                "~~~text",
                _generated_model_text(terra_model),
                "~~~",
                "",
                "### Sol-Generated Mathematical Model",
                "",
                "~~~text",
                _generated_model_text(sol_model),
                "~~~",
                "",
                "### Owner Selection",
                "",
                "Mark exactly one option in each list by changing `[ ]` to `[x]`.",
                "",
                "#### owner_decision",
                "",
                *_owner_option_lines(OWNER_DECISION_OPTIONS, row["owner_decision"]),
                "",
                "#### owner_material",
                "",
                *_owner_option_lines(OWNER_MATERIAL_OPTIONS, row["owner_material"]),
                "",
                "#### owner_mechanism",
                "",
                *_owner_option_lines(OWNER_MECHANISM_OPTIONS, row["owner_mechanism"]),
                "",
            ]
        )
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text("\n".join(markdown_lines).rstrip() + "\n", encoding="utf-8")
    summary = _owner_review_summary(rows)
    summary.update(
        {
            "csv": str(csv_path),
            "markdown": str(markdown_path),
            "excluded_encoding_equivalent_rows": excluded_encoding_rows,
        }
    )
    write_json(campaign_dir / "owner-review" / "owner-review-status.json", summary)
    return summary


def validate_owner_review_packet(*, campaign_dir: Path) -> dict[str, Any]:
    csv_path = campaign_dir / "owner-review" / "owner-review-packet.csv"
    markdown_path = campaign_dir / "owner-review" / "OWNER_REVIEW.md"
    status_path = campaign_dir / "owner-review" / "owner-review-status.json"
    if not csv_path.is_file():
        raise NL4OPTError(f"owner-review packet is missing: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        csv_fields = list(reader.fieldnames or [])
        fieldnames = set(csv_fields)
        required = {"row_id", *OWNER_FIELDS}
        missing_columns = sorted(required - fieldnames)
        if missing_columns:
            raise NL4OPTError(
                "owner-review packet is missing columns: " + ", ".join(missing_columns)
            )
        rows = list(reader)
    if len(rows) > 12:
        raise NL4OPTError(f"owner packet exceeds 12-row cap: {len(rows)}")
    row_ids = [str(row.get("row_id", "")).strip() for row in rows]
    if any(not row_id for row_id in row_ids):
        raise NL4OPTError("owner-review packet contains an empty row_id")
    if len(row_ids) != len(set(row_ids)):
        raise NL4OPTError("owner-review packet contains duplicate row IDs")
    markdown_values = _markdown_owner_values(markdown_path)
    unknown_markdown_rows = sorted(set(markdown_values) - set(row_ids))
    if unknown_markdown_rows:
        raise NL4OPTError(
            "owner-review Markdown contains unknown rows: "
            + ", ".join(unknown_markdown_rows)
        )
    for row in rows:
        row_id = str(row["row_id"]).strip()
        if row_id in markdown_values:
            row.update(markdown_values[row_id])
    write_csv(csv_path, rows, csv_fields)
    summary = _owner_review_summary(rows)
    summary.update(
        {
            "csv": str(csv_path),
            "markdown": str(markdown_path),
        }
    )
    if status_path.is_file():
        previous_status = _read_json_object(status_path)
        excluded_rows = previous_status.get("excluded_encoding_equivalent_rows")
        if isinstance(excluded_rows, list):
            summary["excluded_encoding_equivalent_rows"] = excluded_rows
    write_json(status_path, summary)
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
