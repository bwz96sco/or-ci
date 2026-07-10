from __future__ import annotations

import hashlib
import json
from pathlib import Path


CORPUS_NAMES = [
    "NL4OPT",
    "MAMO_EasyLP",
    "MAMO_ComplexLP",
    "IndustryOR",
    "BWOR",
]

_CORPUS_CONFIG: dict[str, tuple[str, str]] = {
    "NL4OPT": ("NL4OPT_with_optimal_solution.json", "NL4OPT"),
    "MAMO_EasyLP": ("MAMO_EasyLP.json", "MAMO_EASYLP"),
    "MAMO_ComplexLP": ("MAMO_ComplexLP.json", "MAMO_COMPLEXLP"),
    "IndustryOR": ("IndustryOR.json", "INDUSTRYOR"),
    "BWOR": ("BWOR.json", "BWOR"),
}

TEXT_FIELD = "en_question"


def _load_jsonl(path: Path, prefix: str) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for idx, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            text = record.get(TEXT_FIELD, "")
            record["row_id"] = f"{prefix}-{idx:04d}"
            record["statement_sha256"] = hashlib.sha256(
                text.encode("utf-8")
            ).hexdigest()
            rows.append(record)
    return rows


def load_corpus(name: str, data_root: Path) -> list[dict]:
    if name not in _CORPUS_CONFIG:
        raise ValueError(
            f"Unknown corpus {name!r}; valid names: {CORPUS_NAMES}"
        )
    filename, prefix = _CORPUS_CONFIG[name]
    return _load_jsonl(data_root / filename, prefix)
