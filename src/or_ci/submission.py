from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any, Callable


class SubmissionError(RuntimeError):
    """Raised when a submission cannot be imported or does not expose build_model."""


BuildModel = Callable[[dict[str, Any]], Any]


def load_build_model(path: str | Path) -> BuildModel:
    submission_path = Path(path)
    if not submission_path.exists():
        raise SubmissionError(f"submission does not exist: {submission_path}")
    if not submission_path.is_file():
        raise SubmissionError(f"submission is not a file: {submission_path}")

    module = _load_module(submission_path)
    build_model = getattr(module, "build_model", None)
    if not callable(build_model):
        raise SubmissionError("submission must define callable build_model(data)")
    return build_model


def _load_module(path: Path) -> ModuleType:
    digest = hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:16]
    module_name = f"_or_ci_submission_{digest}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise SubmissionError(f"could not create import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise SubmissionError(f"failed to import submission: {exc}") from exc
    return module
