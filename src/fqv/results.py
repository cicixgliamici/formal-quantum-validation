"""Compatibility imports for reports now owned by the domain layer."""

from fqv.domain.reports import (
    CheckResult,
    EquivalenceReport,
    VerificationReport,
)

__all__ = [
    "CheckResult",
    "EquivalenceReport",
    "VerificationReport",
]
