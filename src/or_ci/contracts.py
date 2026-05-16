from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Classification(str, Enum):
    SUCCESS = "SUCCESS"
    SYNTAX_OR_RUNTIME_ERROR = "SYNTAX_OR_RUNTIME_ERROR"
    SOLVER_STATUS_ERROR = "SOLVER_STATUS_ERROR"
    RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL = "RUNNABLE_BUT_WRONG_SEMANTIC_TEST_FAIL"
    UNSUPPORTED_MODEL_FEATURE = "UNSUPPORTED_MODEL_FEATURE"


class VerificationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class CostScalingConfig:
    coefficient_paths: list[str]
    factors: list[float]
    tolerance_abs: float = 1e-6
    tolerance_rel: float = 1e-6


@dataclass(frozen=True)
class ConstraintRelaxationSpec:
    name: str
    paths: list[str]
    factor: float
    objective_relation: str


@dataclass(frozen=True)
class ConstraintRelaxationConfig:
    relaxations: list[ConstraintRelaxationSpec]
    tolerance_abs: float = 1e-6
    tolerance_rel: float = 1e-6


@dataclass(frozen=True)
class ProblemMetadata:
    id: str
    problem_type: str
    instance: dict[str, Any]
    cost_scaling: CostScalingConfig
    constraint_relaxation: ConstraintRelaxationConfig | None = None
    evaluation_only: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VariableIR:
    name: str
    lower_bound: float | str
    upper_bound: float | str
    variable_type: str


@dataclass(frozen=True)
class ObjectiveIR:
    sense: str
    coefficients: dict[str, float]
    constant: float = 0.0


@dataclass(frozen=True)
class ConstraintIR:
    name: str
    sense: str
    rhs: float
    coefficients: dict[str, float]


@dataclass(frozen=True)
class ModelIR:
    variables: list[VariableIR]
    objective: ObjectiveIR
    constraints: list[ConstraintIR]
    summary: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VerificationReport:
    problem_id: str
    submission: str
    status: VerificationStatus
    classification: Classification
    solver_status: dict[str, Any]
    model_ir_summary: dict[str, int]
    checks: list[CheckResult]
    failures: list[dict[str, Any]]
    possible_causes: list[str]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["classification"] = self.classification.value
        return data
