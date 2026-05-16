from __future__ import annotations

import copy
from numbers import Real
from typing import Any

from or_ci.contracts import CostScalingConfig


class ScalingError(ValueError):
    """Raised when configured coefficient paths cannot be scaled."""


def scaled_instance(instance: dict[str, Any], config: CostScalingConfig, factor: float) -> dict[str, Any]:
    return scale_numeric_paths(instance, config.coefficient_paths, factor, context="cost-scaling")


def scale_numeric_paths(
    instance: dict[str, Any],
    paths: list[str],
    factor: float,
    *,
    context: str,
) -> dict[str, Any]:
    scaled = copy.deepcopy(instance)
    total_scaled = 0
    for path in paths:
        parts = path.split(".")
        if parts and parts[0] == "instance":
            parts = parts[1:]
        else:
            raise ScalingError(f"{context} path must start with instance: {path}")
        count = _scale_at_path(scaled, parts, factor)
        if count == 0:
            raise ScalingError(f"{context} path did not find numeric values: {path}")
        total_scaled += count
    if total_scaled == 0:
        raise ScalingError(f"{context} configuration did not scale any numeric values")
    return scaled


def _scale_at_path(node: Any, parts: list[str], factor: float) -> int:
    if not parts:
        return _scale_numeric_subtree(node, factor)

    head = parts[0]
    tail = parts[1:]
    if isinstance(node, dict):
        if head not in node:
            return 0
        if not tail:
            before = node[head]
            node[head], count = _scaled_subtree(before, factor)
            return count
        return _scale_at_path(node[head], tail, factor)

    if isinstance(node, list):
        if head == "*":
            return sum(_scale_at_path(item, tail, factor) for item in node)
        if head.isdigit():
            index = int(head)
            if index >= len(node):
                return 0
            return _scale_at_path(node[index], tail, factor)
        return sum(_scale_at_path(item, parts, factor) for item in node)

    return 0


def _scale_numeric_subtree(node: Any, factor: float) -> int:
    _, count = _scaled_subtree(node, factor)
    return count


def _scaled_subtree(node: Any, factor: float) -> tuple[Any, int]:
    if _is_number(node):
        return float(node) * factor, 1
    if isinstance(node, dict):
        count = 0
        updated = {}
        for key, value in node.items():
            updated_value, scaled_count = _scaled_subtree(value, factor)
            updated[key] = updated_value
            count += scaled_count
        node.clear()
        node.update(updated)
        return node, count
    if isinstance(node, list):
        count = 0
        for index, value in enumerate(node):
            updated_value, scaled_count = _scaled_subtree(value, factor)
            node[index] = updated_value
            count += scaled_count
        return node, count
    return node, 0


def _is_number(value: Any) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool)
