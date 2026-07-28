"""Structural validation helpers for raw contract objects."""

from __future__ import annotations

from typing import Any, Mapping


class InvalidContractError(ValueError):
    """Raised when raw contract data cannot enter the domain model."""


def require_mapping(value: object, *, field_name: str) -> Mapping[str, Any]:
    """Require one JSON object and preserve its field context."""

    if not isinstance(value, dict):
        raise InvalidContractError(f"{field_name} must be a JSON object")
    return value


def require_number_in_unit_interval(value: object, *, field_name: str) -> float:
    """Validate a non-Boolean numeric probability-like value."""

    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not 0.0 <= float(value) <= 1.0
    ):
        raise InvalidContractError(f"{field_name} must be in [0, 1]")
    return float(value)


def require_nonnegative_number(value: object, *, field_name: str) -> float:
    """Validate a nonnegative tolerance."""

    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or float(value) < 0.0
    ):
        raise InvalidContractError(f"{field_name} must be non-negative")
    return float(value)
