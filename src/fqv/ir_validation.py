"""Compatibility wrapper for raw IR validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from fqv.ir.raw import load_raw_ir
from fqv.ir.validation import InvalidIrError, check_ir


def validate_ir(data: Mapping[str, Any]) -> None:
    """Validate raw IR while preserving the former no-return API."""

    check_ir(data)


def load_ir(path: str | Path) -> dict[str, Any]:
    """Load and validate raw IR for compatibility callers."""

    try:
        raw = load_raw_ir(path)
    except ValueError as error:
        raise InvalidIrError(str(error)) from error
    check_ir(raw)
    return raw


__all__ = ["InvalidIrError", "load_ir", "validate_ir"]
