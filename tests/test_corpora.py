from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from or_ci.corpora import CORPUS_NAMES, load_corpus, _load_jsonl

FIXTURES = Path(__file__).parent / "fixtures" / "corpora"
REAL_DATA_ROOT = Path("/Users/zhangbowen/Projects/OR/code/or_llm_agent/data/datasets")


def test_load_tiny_fixture():
    rows = _load_jsonl(FIXTURES / "tiny_corpus.jsonl", "TINY")
    assert len(rows) == 2
    assert rows[0]["row_id"] == "TINY-0000"
    assert rows[1]["row_id"] == "TINY-0001"
    for row in rows:
        assert "statement_sha256" in row
        assert len(row["statement_sha256"]) == 64
    expected_hash = hashlib.sha256(
        "Minimize total cost subject to demand constraints.".encode("utf-8")
    ).hexdigest()
    assert rows[0]["statement_sha256"] == expected_hash


def test_load_corpus_invalid_name():
    with pytest.raises(ValueError, match="Unknown corpus"):
        load_corpus("NONEXISTENT", FIXTURES)


def test_corpus_names_list():
    assert len(CORPUS_NAMES) == 5
    assert "NL4OPT" in CORPUS_NAMES
    assert "BWOR" in CORPUS_NAMES


EXPECTED_COUNTS = {
    "NL4OPT": 245,
    "MAMO_EasyLP": 652,
    "MAMO_ComplexLP": 211,
    "IndustryOR": 100,
    "BWOR": 82,
}


@pytest.mark.skipif(
    not REAL_DATA_ROOT.is_dir(),
    reason="Real dataset root not available",
)
@pytest.mark.parametrize("name,expected", EXPECTED_COUNTS.items())
def test_real_corpus_row_counts(name: str, expected: int):
    rows = load_corpus(name, REAL_DATA_ROOT)
    assert len(rows) == expected
    for row in rows:
        assert "row_id" in row
        assert "statement_sha256" in row
