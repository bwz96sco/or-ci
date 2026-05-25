from __future__ import annotations

from gurobipy import GRB

from or_ci.model_ir import UnsupportedModelFeature, extract_model_ir


class FakeVar:
    def __init__(self, name: str, lower_bound: float = 0.0, upper_bound: float = 10.0, variable_type: str = GRB.CONTINUOUS):
        self.VarName = name
        self.LB = lower_bound
        self.UB = upper_bound
        self.VType = variable_type


class FakeExpr:
    def __init__(self, terms: list[tuple[FakeVar, float]], constant: float = 0.0):
        self._terms = terms
        self._constant = constant

    def size(self) -> int:
        return len(self._terms)

    def getVar(self, index: int) -> FakeVar:
        return self._terms[index][0]

    def getCoeff(self, index: int) -> float:
        return self._terms[index][1]

    def getConstant(self) -> float:
        return self._constant


class FakeQuadExpr:
    def __init__(
        self,
        linear_terms: list[tuple[FakeVar, float]],
        quadratic_terms: list[tuple[FakeVar, FakeVar, float]],
        constant: float = 0.0,
    ):
        self._linear = FakeExpr(linear_terms, constant=constant)
        self._quadratic_terms = quadratic_terms

    def size(self) -> int:
        return len(self._quadratic_terms)

    def getVar1(self, index: int) -> FakeVar:
        return self._quadratic_terms[index][0]

    def getVar2(self, index: int) -> FakeVar:
        return self._quadratic_terms[index][1]

    def getCoeff(self, index: int) -> float:
        return self._quadratic_terms[index][2]

    def getLinExpr(self) -> FakeExpr:
        return self._linear

    def getConstant(self) -> float:
        return self._linear.getConstant()


class FakeConstr:
    def __init__(self, name: str, sense: str, rhs: float, row: FakeExpr):
        self.ConstrName = name
        self.Sense = sense
        self.RHS = rhs
        self.row = row


class FakeModel:
    NumSOS = 0
    NumQConstrs = 0
    NumGenConstrs = 0
    NumPWLObjVars = 0
    NumQNZs = 0
    IsMultiObj = 0

    def __init__(self):
        self.x = FakeVar("x")
        self.y = FakeVar("y", upper_bound=GRB.INFINITY)
        self.ModelSense = GRB.MAXIMIZE
        self._objective = FakeExpr([(self.x, 2.0), (self.y, -3.0)], constant=5.0)
        self._constraints = [
            FakeConstr("c1", "<", 4.0, FakeExpr([(self.x, 1.0), (self.y, 1.0)])),
            FakeConstr("c2", ">", 1.0, FakeExpr([(self.x, -1.0), (self.y, 2.0)])),
        ]

    def update(self) -> None:
        return None

    def getVars(self) -> list[FakeVar]:
        return [self.x, self.y]

    def getConstrs(self) -> list[FakeConstr]:
        return self._constraints

    def getRow(self, constr: FakeConstr) -> FakeExpr:
        return constr.row

    def getObjective(self) -> FakeExpr:
        return self._objective


def test_extract_model_ir_preserves_linear_model_details() -> None:
    model_ir = extract_model_ir(FakeModel())

    assert model_ir.objective.sense == "max"
    assert model_ir.objective.coefficients == {"x": 2.0, "y": -3.0}
    assert model_ir.objective.constant == 5.0
    assert model_ir.variables[1].upper_bound == "inf"
    assert model_ir.constraints[0].coefficients == {"x": 1.0, "y": 1.0}
    assert model_ir.constraints[1].coefficients == {"x": -1.0, "y": 2.0}
    assert model_ir.summary == {
        "variables": 2,
        "constraints": 2,
        "integer_variables": 0,
        "binary_variables": 0,
        "quadratic_objective_terms": 0,
    }


def test_extract_model_ir_preserves_quadratic_objective_terms() -> None:
    model = FakeModel()
    model.NumQNZs = 2
    model._objective = FakeQuadExpr(
        [(model.x, 1.0)],
        [(model.x, model.x, 2.0), (model.y, model.x, -4.0)],
        constant=3.0,
    )

    model_ir = extract_model_ir(model)

    assert model_ir.objective.coefficients == {"x": 1.0}
    assert model_ir.objective.constant == 3.0
    assert [term.__dict__ for term in model_ir.objective.quadratic_terms] == [
        {"var1": "x", "var2": "x", "coefficient": 2.0},
        {"var1": "x", "var2": "y", "coefficient": -4.0},
    ]
    assert model_ir.summary["quadratic_objective_terms"] == 2


def test_extract_model_ir_rejects_unsupported_features() -> None:
    model = FakeModel()
    model.NumQConstrs = 1

    try:
        extract_model_ir(model)
    except UnsupportedModelFeature as exc:
        assert "quadratic constraints" in str(exc)
    else:
        raise AssertionError("expected UnsupportedModelFeature")
