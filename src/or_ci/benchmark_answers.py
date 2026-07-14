from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping


NO_BEST_SOLUTION_TEXT = {
    "no best solution",
    "no feasible solution",
    "no optimal solution",
    "no solution",
    "infeasible",
    "unbounded",
}


@dataclass(frozen=True)
class AnswerPolicy:
    name: str
    status_sentinels: tuple[float, ...]
    absolute_tolerance: float
    relative_tolerance: float
    solver_absolute_tolerance: float
    solver_relative_tolerance: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status_sentinels": list(self.status_sentinels),
            "absolute_tolerance": self.absolute_tolerance,
            "relative_tolerance": self.relative_tolerance,
            "solver_absolute_tolerance": self.solver_absolute_tolerance,
            "solver_relative_tolerance": self.solver_relative_tolerance,
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> AnswerPolicy:
        sentinels = payload.get("status_sentinels")
        if not isinstance(sentinels, list) or not sentinels:
            raise ValueError("answer policy status_sentinels must be a non-empty list")
        absolute = float(payload.get("absolute_tolerance", 1e-7))
        relative = float(payload.get("relative_tolerance", 1e-7))
        solver_absolute = float(payload.get("solver_absolute_tolerance", absolute))
        solver_relative = float(payload.get("solver_relative_tolerance", relative))
        if min(absolute, relative, solver_absolute, solver_relative) < 0:
            raise ValueError("answer policy tolerances must be non-negative")
        return cls(
            name=str(payload.get("name", "campaign_answer_policy")),
            status_sentinels=tuple(float(value) for value in sentinels),
            absolute_tolerance=absolute,
            relative_tolerance=relative,
            solver_absolute_tolerance=solver_absolute,
            solver_relative_tolerance=solver_relative,
        )


NL4OPT_ANSWER_POLICY = AnswerPolicy(
    name="nl4opt_v1",
    status_sentinels=(-99999.0,),
    absolute_tolerance=1e-7,
    relative_tolerance=1e-7,
    solver_absolute_tolerance=1e-6,
    solver_relative_tolerance=1e-6,
)

MAMO_EASYLP_ANSWER_POLICY = AnswerPolicy(
    name="mamo_easylp_v1",
    status_sentinels=(-9999.0, -99999.0),
    absolute_tolerance=0.005,
    relative_tolerance=1e-6,
    solver_absolute_tolerance=0.005,
    solver_relative_tolerance=1e-6,
)


_GUROBI_TERMINAL_STATUS_CLASSES = {
    2: "optimal",
    3: "infeasible",
    4: "infeasible_or_unbounded",
    5: "unbounded",
}


def canonical_solver_status(value: Any) -> str:
    """Normalize supported textual and native Gurobi terminal statuses."""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)) and float(value).is_integer():
        code = int(value)
        return _GUROBI_TERMINAL_STATUS_CLASSES.get(code, f"gurobi_status_{code}")
    text = str(value).strip().lower()
    try:
        number = float(text)
    except ValueError:
        return text
    if number.is_integer():
        code = int(number)
        return _GUROBI_TERMINAL_STATUS_CLASSES.get(code, f"gurobi_status_{code}")
    return text


def canonical_answer(
    value: Any,
    *,
    policy: AnswerPolicy = NL4OPT_ANSWER_POLICY,
) -> tuple[str, float | None]:
    text = str(value).strip()
    lowered = text.lower()
    if lowered in NO_BEST_SOLUTION_TEXT:
        return "no_best_solution", None
    try:
        number = float(text.replace(",", ""))
    except ValueError:
        return lowered, None
    if any(
        math.isclose(number, sentinel, rel_tol=0.0, abs_tol=1e-9)
        for sentinel in policy.status_sentinels
    ):
        return "no_best_solution", None
    return "numeric", number


def answers_equal(
    left: Any,
    right: Any,
    *,
    tolerance: float | None = None,
    policy: AnswerPolicy = NL4OPT_ANSWER_POLICY,
) -> bool:
    left_kind, left_number = canonical_answer(left, policy=policy)
    right_kind, right_number = canonical_answer(right, policy=policy)
    if left_kind != right_kind:
        return False
    if left_kind != "numeric":
        return True
    assert left_number is not None and right_number is not None
    absolute = tolerance if tolerance is not None else policy.absolute_tolerance
    relative = tolerance if tolerance is not None else policy.relative_tolerance
    return math.isclose(left_number, right_number, rel_tol=relative, abs_tol=absolute)


def answer_relation(
    left: Any,
    right: Any,
    *,
    policy: AnswerPolicy = NL4OPT_ANSWER_POLICY,
) -> str:
    if not answers_equal(left, right, policy=policy):
        return "semantic_difference"
    if str(left).strip() != str(right).strip():
        return "encoding_equivalent"
    return "unchanged"


def semantic_answer(
    value: Any,
    *,
    policy: AnswerPolicy = NL4OPT_ANSWER_POLICY,
) -> str:
    kind, _ = canonical_answer(value, policy=policy)
    if kind == "no_best_solution":
        return "No Best Solution"
    return str(value).strip()


def answer_encoding(
    value: Any,
    *,
    policy: AnswerPolicy = NL4OPT_ANSWER_POLICY,
) -> str:
    raw = str(value).strip()
    kind, _ = canonical_answer(value, policy=policy)
    if kind != "no_best_solution":
        return "literal"
    try:
        number = float(raw.replace(",", ""))
    except ValueError:
        return "literal_status"
    for sentinel in policy.status_sentinels:
        if math.isclose(number, sentinel, rel_tol=0.0, abs_tol=1e-9):
            magnitude = str(abs(int(sentinel))) if sentinel.is_integer() else str(abs(sentinel))
            return f"sentinel_minus_{magnitude}"
    return "literal_status"


def result_matches_answer(
    result: Mapping[str, Any],
    answer: Any,
    *,
    tolerance: float | None = None,
    policy: AnswerPolicy = NL4OPT_ANSWER_POLICY,
) -> bool:
    answer_kind, answer_number = canonical_answer(answer, policy=policy)
    status = canonical_solver_status(result.get("status", ""))
    if answer_kind == "no_best_solution":
        return status in {
            "infeasible",
            "unbounded",
            "infeasible_or_unbounded",
            "strict_inequality_infimum_not_attained",
            "no_attained_minimum_strict_continuous",
            "no_attained_maximum_strict_continuous",
        }
    if answer_kind != "numeric" or status != "optimal" or answer_number is None:
        return False
    objective = result.get("objective")
    if not isinstance(objective, (int, float)):
        return False
    absolute = tolerance if tolerance is not None else policy.solver_absolute_tolerance
    relative = tolerance if tolerance is not None else policy.solver_relative_tolerance
    return math.isclose(float(objective), answer_number, rel_tol=relative, abs_tol=absolute)
