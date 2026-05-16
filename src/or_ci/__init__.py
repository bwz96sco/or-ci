"""OR-CI Phase 1 verification package."""

from or_ci.contracts import Classification, VerificationStatus
from or_ci.verifier import verify

__all__ = ["Classification", "VerificationStatus", "verify"]
