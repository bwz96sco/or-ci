from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class FormulationAdapterError(ValueError):
    """Raised when a structured formulation cannot be materialized."""


MINIMIZE_ALIASES = {"min", "minimize", "minimized", "minimum", "reduce", "decrease"}
MAXIMIZE_ALIASES = {"max", "maximize", "maximized", "maximum"}
TEXT_NUMBER_ALIASES = {
    "one": 1.0,
    "twice": 2.0,
    "two": 2.0,
    "three times": 3.0,
    "three": 3.0,
    "four": 4.0,
    "five": 5.0,
    "six": 6.0,
    "seven": 7.0,
    "eight": 8.0,
    "nine": 9.0,
    "ten": 10.0,
    "twenty": 20.0,
}

SUBMISSION_TEMPLATE = '''from __future__ import annotations

import gurobipy as gp
from gurobipy import GRB


def build_model(data: dict) -> gp.Model:
    model = gp.Model()
    variables = {}
    for spec in data["variables"]:
        upper_bound = spec.get("upper_bound")
        variables[spec["name"]] = model.addVar(
            lb=float(spec.get("lower_bound", 0.0)),
            ub=GRB.INFINITY if upper_bound is None else float(upper_bound),
            vtype=GRB.CONTINUOUS,
            name=spec["gurobi_name"],
        )
    model.update()

    objective = gp.LinExpr()
    for name, coefficient in data["objective"]["coefficients"].items():
        objective.addTerms(float(coefficient), variables[name])
    sense = GRB.MAXIMIZE if data["objective"]["sense"] == "max" else GRB.MINIMIZE
    model.setObjective(objective, sense)

    for constraint in data["constraints"]:
        expr = gp.LinExpr()
        for name, coefficient in constraint["coefficients"].items():
            expr.addTerms(float(coefficient), variables[name])
        rhs = float(constraint["rhs"])
        if constraint["sense"] == "<=":
            model.addConstr(expr <= rhs, name=constraint["name"])
        elif constraint["sense"] == ">=":
            model.addConstr(expr >= rhs, name=constraint["name"])
        elif constraint["sense"] == "=":
            model.addConstr(expr == rhs, name=constraint["name"])
        else:
            raise ValueError(f"unsupported constraint sense: {constraint['sense']}")
    return model
'''


def materialize_formulation(
    formulation_path: str | Path,
    *,
    problem_id: str,
    output_dir: str | Path,
    record_id: str,
    manual_constraints: dict[int, dict[str, str]] | None = None,
) -> tuple[Path, Path]:
    formulation_file = Path(formulation_path)
    formulation = json.loads(formulation_file.read_text(encoding="utf-8"))
    problem = build_problem_metadata(
        formulation,
        problem_id=problem_id,
        record_id=record_id,
        formulation_path=formulation_file,
        manual_constraints=manual_constraints or {},
    )

    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    problem_path = target / "problem.json"
    submission_path = target / "submission.py"
    problem_path.write_text(json.dumps(problem, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    submission_path.write_text(SUBMISSION_TEMPLATE, encoding="utf-8")
    return problem_path, submission_path


def build_problem_metadata(
    formulation: dict[str, Any],
    *,
    problem_id: str,
    record_id: str,
    formulation_path: Path,
    manual_constraints: dict[int, dict[str, str]],
) -> dict[str, Any]:
    if not problem_id.startswith("BWOR-"):
        raise FormulationAdapterError("materialized problem_id must start with BWOR-")

    variables = _variables(formulation)
    objective = _objective(formulation, variables)
    constraints = _constraints(formulation, variables, manual_constraints)
    return {
        "id": problem_id,
        "problem_type": "LP",
        "instance": {
            "variables": [
                {
                    "name": name,
                    "gurobi_name": _gurobi_name(name, index),
                    "lower_bound": 0.0,
                    "upper_bound": None,
                }
                for index, name in enumerate(variables)
            ],
            "objective": objective,
            "constraints": constraints,
        },
        "metamorphic": {
            "cost_scaling": {
                "coefficient_paths": ["instance.objective.coefficients"],
                "factors": [2.0],
                "tolerance_abs": 1e-6,
                "tolerance_rel": 1e-6,
            }
        },
        "evaluation_only": {
            "record_id": record_id,
            "formulation_path": str(formulation_path),
            "adapter_non_claim": "materialized verifier input is not proof of source-statement fidelity",
        },
    }


def _variables(formulation: dict[str, Any]) -> list[str]:
    raw = formulation.get("vars")
    if not isinstance(raw, list) or not raw:
        raise FormulationAdapterError("formulation.vars must be a non-empty list")
    variables = []
    seen = set()
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise FormulationAdapterError("formulation.vars entries must be non-empty strings")
        name = item.strip()
        if name in seen:
            raise FormulationAdapterError(f"duplicate variable name: {name}")
        seen.add(name)
        variables.append(name)
    return variables


def _objective(formulation: dict[str, Any], variables: list[str]) -> dict[str, Any]:
    raw = formulation.get("obj_declaration")
    if not isinstance(raw, dict):
        raise FormulationAdapterError("obj_declaration must be an object")
    direction = _objective_sense(raw.get("direction"))
    objective_type = raw.get("type")
    if objective_type == "objective":
        terms = raw.get("terms")
        if not isinstance(terms, dict) or not terms:
            raise FormulationAdapterError("objective terms must be a non-empty object")
        coefficients = _coefficients(variables, terms)
    elif objective_type == "objvar":
        refs = raw.get("vars")
        if not isinstance(refs, list) or not refs:
            raise FormulationAdapterError("objvar objective vars must be a non-empty list")
        coefficients = _coefficients(variables, {str(ref): 1.0 for ref in refs})
    else:
        raise FormulationAdapterError(f"unsupported objective type: {objective_type!r}")
    return {"sense": direction, "coefficients": coefficients}


def _constraints(
    formulation: dict[str, Any],
    variables: list[str],
    manual_constraints: dict[int, dict[str, str]],
) -> list[dict[str, Any]]:
    raw_constraints = formulation.get("const_declarations")
    if not isinstance(raw_constraints, list):
        raise FormulationAdapterError("const_declarations must be a list")

    constraints = []
    for index, raw in enumerate(raw_constraints):
        if not isinstance(raw, dict):
            raise FormulationAdapterError(f"constraint {index}: must be an object")
        constraint = _constraint(raw, variables, index, manual_constraints)
        constraint["name"] = f"c_{index:03d}_{constraint.pop('kind')}"
        constraints.append(constraint)
    return constraints


def _constraint(
    raw: dict[str, Any],
    variables: list[str],
    index: int,
    manual_constraints: dict[int, dict[str, str]],
) -> dict[str, Any]:
    ctype = raw.get("type")
    operator = str(raw.get("operator") or "")
    if ctype == "linear":
        rhs = _required_number(raw.get("limit"), f"constraint {index}: limit")
        return {
            "kind": "linear",
            "sense": _sense(operator),
            "rhs": rhs,
            "coefficients": _coefficients(variables, _required_terms(raw, index)),
        }
    if ctype == "lowerbound":
        var = _resolve_var(str(raw.get("var") or ""), variables)
        rhs = _required_number(raw.get("limit"), f"constraint {index}: lowerbound")
        return {"kind": "lowerbound", "sense": ">=", "rhs": rhs, "coefficients": {var: 1.0}}
    if ctype == "upperbound":
        var = _resolve_var(str(raw.get("var") or ""), variables)
        rhs = _required_number(raw.get("limit"), f"constraint {index}: upperbound")
        return {"kind": "upperbound", "sense": "<=", "rhs": rhs, "coefficients": {var: 1.0}}
    if ctype == "sum":
        rhs = _required_number(raw.get("limit"), f"constraint {index}: sum limit")
        return {"kind": "sum", "sense": _sense(operator), "rhs": rhs, "coefficients": {name: 1.0 for name in variables}}
    if ctype == "xby":
        x_var = _resolve_var(str(raw.get("x_var") or ""), variables)
        y_var = _resolve_var(str(raw.get("y_var") or ""), variables)
        param = _required_number(raw.get("param"), f"constraint {index}: xby param")
        return {
            "kind": "xby",
            "sense": _sense(operator),
            "rhs": 0.0,
            "coefficients": _non_zero({x_var: 1.0, y_var: -param}),
        }
    if ctype == "ratio":
        var = _resolve_var(str(raw.get("var") or ""), variables)
        share = _required_number(raw.get("limit"), f"constraint {index}: ratio limit")
        if share < 0.0 or share > 1.0:
            raise FormulationAdapterError(f"constraint {index}: ratio limit must be in [0, 1]")
        coefficients = {name: -share for name in variables}
        coefficients[var] = coefficients.get(var, 0.0) + 1.0
        return {"kind": "ratio", "sense": _sense(operator), "rhs": 0.0, "coefficients": _non_zero(coefficients)}
    if ctype == "xy":
        manual = manual_constraints.get(index)
        if manual is None:
            raise FormulationAdapterError(f"constraint {index}: xy requires a manual constraint spec")
        left = _resolve_var(manual.get("left_var", ""), variables)
        right = _resolve_var(manual.get("right_var", ""), variables)
        return {
            "kind": "xy_manual",
            "sense": _sense(manual.get("relation_operator", "")),
            "rhs": 0.0,
            "coefficients": _non_zero({left: 1.0, right: -1.0}),
        }
    raise FormulationAdapterError(f"constraint {index}: unsupported constraint type {ctype!r}")


def _required_terms(raw: dict[str, Any], index: int) -> dict[str, Any]:
    terms = raw.get("terms")
    if not isinstance(terms, dict) or not terms:
        raise FormulationAdapterError(f"constraint {index}: terms must be a non-empty object")
    return terms


def _coefficients(variables: list[str], terms: dict[str, Any]) -> dict[str, float]:
    coefficients = {name: 0.0 for name in variables}
    for reference, raw_value in terms.items():
        var = _resolve_var(str(reference), variables)
        coefficients[var] += _required_number(raw_value, f"coefficient for {reference!r}")
    return _non_zero(coefficients)


def _non_zero(coefficients: dict[str, float]) -> dict[str, float]:
    return {name: value for name, value in coefficients.items() if abs(value) > 1e-12}


def _objective_sense(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in MINIMIZE_ALIASES:
        return "min"
    if normalized in MAXIMIZE_ALIASES:
        return "max"
    raise FormulationAdapterError(f"unsupported objective direction: {value!r}")


def _sense(value: str) -> str:
    normalized = value.strip().upper()
    if normalized == "LESS_OR_EQUAL":
        return "<="
    if normalized == "GREATER_OR_EQUAL":
        return ">="
    if normalized in {"EQUAL", "EQUAL_TO"}:
        return "="
    raise FormulationAdapterError(f"unsupported constraint operator: {value!r}")


def _required_number(value: Any, field: str) -> float:
    parsed = _parse_number(value)
    if parsed is None:
        raise FormulationAdapterError(f"{field} must be numeric")
    return parsed


def _parse_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    text = str(value).strip().lower().replace(",", "").replace("$", "")
    if not text:
        return None
    if text in TEXT_NUMBER_ALIASES:
        return TEXT_NUMBER_ALIASES[text]
    if text.endswith("%"):
        try:
            return float(text[:-1]) / 100.0
        except ValueError:
            return None
    try:
        return float(text)
    except ValueError:
        return None


def _resolve_var(reference: str, variables: list[str]) -> str:
    if reference in variables:
        return reference
    normalized_reference = _normalize_name(reference)
    normalized = {_normalize_name(name): name for name in variables}
    if normalized_reference in normalized:
        return normalized[normalized_reference]

    reference_tokens = _expanded_tokens(normalized_reference)
    candidates = []
    for name in variables:
        variable_tokens = _expanded_tokens(_normalize_name(name))
        if reference_tokens and (reference_tokens <= variable_tokens or variable_tokens <= reference_tokens):
            candidates.append(name)
    if len(candidates) == 1:
        return candidates[0]
    raise FormulationAdapterError(f"unresolved variable reference: {reference!r}")


def _normalize_name(value: str) -> str:
    tokens = re.sub(r"[^a-z0-9]+", " ", value.lower()).split()
    normalized = []
    for token in tokens:
        if len(token) > 4 and token.endswith("ies"):
            normalized.append(token[:-3] + "y")
        elif len(token) > 4 and token.endswith(("ches", "shes")):
            normalized.append(token[:-2])
        elif len(token) > 3 and token.endswith(("xes", "ses", "zes")):
            normalized.append(token[:-2])
        elif len(token) > 3 and token.endswith("s"):
            normalized.append(token[:-1])
        else:
            normalized.append(token)
    return " ".join(normalized)


def _expanded_tokens(normalized: str) -> set[str]:
    tokens: set[str] = set()
    for token in normalized.split():
        tokens.add(token)
        if token.endswith("y"):
            tokens.add(token[:-1] + "ie")
        if token.endswith("ie"):
            tokens.add(token[:-2] + "y")
    return tokens


def _gurobi_name(name: str, index: int) -> str:
    suffix = re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_").lower()
    if not suffix:
        suffix = "var"
    return f"x_{index}_{suffix}"
