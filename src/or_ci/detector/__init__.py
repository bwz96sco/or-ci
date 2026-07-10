from __future__ import annotations

from or_ci.detector.layer0_rules import detect_source_text as detect_layer0
from or_ci.detector.v1_rules import detect_source_artifact as detect_source_artifact_v1
from or_ci.detector.v1_rules import detect_source_text as detect_source_text_v1
from or_ci.detector.v2_rules import detect_v2

__all__ = [
    "detect_layer0",
    "detect_source_text_v1",
    "detect_source_artifact_v1",
    "detect_v2",
]
