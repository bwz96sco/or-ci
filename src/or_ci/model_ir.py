from __future__ import annotations

from typing import Any

from gurobipy import GRB

from or_ci.contracts import ConstraintIR, ModelIR, ObjectiveIR, VariableIR


class UnsupportedModelFeature(RuntimeError):
    """Raised when a Gurobi model uses features outside Phase 1 ModelIR."""


_UNSUPPORTED_MODEL_ATTRIBUTES = {
    "NumSOS": "SOS constraints",
    "NumQConstrs": "quadratic constraints",
    "NumGenConstrs": "general constraints",
    "NumPWLObjVars": "piecewise-linear objectives",
    "NumQNZs": "quadratic objective terms",
    "IsMultiObj": "multiple objectives",
}


def extract_model_ir(model: Any) -> ModelIR:
    model.update()
    _reject_unsupported_features(model)

    variables = [_extract_variable(var) for var in model.getVars()]
    variable_names = {var.name for var in variables}
    objective = _extract_objective(model, variable_names)
    constraints = [_extract_constraint(model, constr, variable_names) for constr in model.getConstrs()]

    return ModelIR(
        variables=variables,
        objective=objective,
        constraints=constraints,
        summary={
            "variables": len(variables),
            "constraints": len(constraints),
            "integer_variables": sum(1 for var in variables if var.variable_type == GRB.INTEGER),
            "binary_variables": sum(1 for var in variables if var.variable_type == GRB.BINARY),
        },
    )


def _reject_unsupported_features(model: Any) -> None:
    unsupported = []
    for attr_name, label in _UNSUPPORTED_MODEL_ATTRIBUTES.items():
        value = _get_attr(model, attr_name, 0)
        if value:
            unsupported.append(label)
    if unsupported:
        raise UnsupportedModelFeature("unsupported model features: " + ", ".join(unsupported))


def _extract_variable(var: Any) -> VariableIR:
    return VariableIR(
        name=str(_get_attr(var, "VarName")),
        lower_bound=_json_bound(float(_get_attr(var, "LB"))),
        upper_bound=_json_bound(float(_get_attr(var, "UB"))),
        variable_type=str(_get_attr(var, "VType")),
    )


def _extract_objective(model: Any, variable_names: set[str]) -> ObjectiveIR:
    sense_value = int(_get_attr(model, "ModelSense", GRB.MINIMIZE))
    sense = "max" if sense_value == GRB.MAXIMIZE else "min"
    objective = model.getObjective()
    coefficients = _linear_expression_coefficients(objective, variable_names)
    constant = _expression_constant(objective)
    return ObjectiveIR(sense=sense, coefficients=coefficients, constant=constant)


def _extract_constraint(model: Any, constr: Any, variable_names: set[str]) -> ConstraintIR:
    row = model.getRow(constr)
    name = str(_get_attr(constr, "ConstrName"))
    return ConstraintIR(
        name=name,
        sense=str(_get_attr(constr, "Sense")),
        rhs=float(_get_attr(constr, "RHS")),
        coefficients=_linear_expression_coefficients(row, variable_names),
    )


def _linear_expression_coefficients(expr: Any, variable_names: set[str]) -> dict[str, float]:
    if not all(hasattr(expr, attr) for attr in ("size", "getVar", "getCoeff")):
        raise UnsupportedModelFeature(f"unsupported expression type: {type(expr).__name__}")

    coefficients: dict[str, float] = {}
    for index in range(expr.size()):
        var = expr.getVar(index)
        name = str(_get_attr(var, "VarName"))
        if name not in variable_names:
            raise UnsupportedModelFeature(f"expression references unknown variable: {name}")
        coefficients[name] = coefficients.get(name, 0.0) + float(expr.getCoeff(index))
    return {name: coeff for name, coeff in coefficients.items() if coeff != 0.0}


def _expression_constant(expr: Any) -> float:
    get_constant = getattr(expr, "getConstant", None)
    if callable(get_constant):
        return float(get_constant())
    return 0.0


def _get_attr(obj: Any, attr_name: str, default: Any = None) -> Any:
    if hasattr(obj, attr_name):
        return getattr(obj, attr_name)
    lower_name = attr_name[0].lower() + attr_name[1:]
    if hasattr(obj, lower_name):
        return getattr(obj, lower_name)
    get_attr = getattr(obj, "getAttr", None)
    if callable(get_attr):
        try:
            return get_attr(attr_name)
        except Exception:
            if default is not None:
                return default
            raise
    if default is not None:
        return default
    raise AttributeError(f"{type(obj).__name__} has no attribute {attr_name}")


def _json_bound(value: float) -> float | str:
    if value >= GRB.INFINITY / 2:
        return "inf"
    if value <= -GRB.INFINITY / 2:
        return "-inf"
    return value
