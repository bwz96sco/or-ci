from __future__ import annotations

from pathlib import Path

import gurobipy as gp
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
BWOR_FIXTURES = REPO_ROOT / "tests" / "fixtures" / "bwor"


@pytest.fixture(scope="session")
def gurobi_license_status() -> tuple[bool, str]:
    try:
        env = gp.Env(empty=True)
        env.setParam("OutputFlag", 0)
        env.start()
        model = gp.Model(env=env)
        model.dispose()
        env.dispose()
    except gp.GurobiError as exc:
        return False, str(exc)
    return True, ""


@pytest.fixture
def require_gurobi_license(gurobi_license_status: tuple[bool, str]) -> None:
    available, message = gurobi_license_status
    if not available:
        pytest.skip(f"Gurobi license unavailable: {message}")
