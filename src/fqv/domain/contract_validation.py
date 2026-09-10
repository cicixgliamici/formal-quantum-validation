"""Structural validation helpers for raw contract objects."""

from __future__ import annotations

from math import isfinite
from typing import Any, Mapping


class InvalidContractError(ValueError):
    """Raised when a specification cannot be interpreted as a valid contract.

    Parser helpers raise this for malformed fields or unnormalized vectors;
    the executable state check also uses it for invalid direct Python inputs.
    This differs from a CheckResult with passed=False: that result describes a
    valid specification whose requested behavior the circuit did not satisfy.
    """


def require_mapping(value: object, *, field_name: str) -> Mapping[str, Any]:
    """Require one JSON object and preserve its field context."""

    if not isinstance(value, dict):
        raise InvalidContractError(f"{field_name} must be a JSON object")
    return value


def require_fields(
    value: Mapping[str, Any],
    *,
    required: set[str],
    optional: set[str] | None = None,
    field_name: str,
) -> None:
    """Reject missing and unknown fields instead of silently changing intent."""
    missing = required - value.keys()
    unexpected = value.keys() - required - (optional or set())
    if missing or unexpected:
        raise InvalidContractError(
            f"{field_name}: missing fields {sorted(missing)}, "
            f"unexpected fields {sorted(unexpected, key=str)}"
        )


def require_number_in_unit_interval(value: object, *, field_name: str) -> float:
    """Validate a non-Boolean numeric probability-like value."""

    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not 0 <= value <= 1
    ):
        raise InvalidContractError(f"{field_name} must be in [0, 1]")
    return float(value)


def require_nonnegative_number(value: object, *, field_name: str) -> float:
    """Validate a nonnegative tolerance."""

    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or value < 0
    ):
        raise InvalidContractError(f"{field_name} must be non-negative")
    # Large JSON integers can overflow float conversion; report a domain error.
    try:
        result = float(value)
    except OverflowError as error:
        raise InvalidContractError(f"{field_name} must be finite") from error
    if not isfinite(result):
        raise InvalidContractError(f"{field_name} must be finite")
    return result
