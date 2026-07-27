"""Formal Quantum Validation.

The package root intentionally avoids eager Qiskit imports. Contract parsing
and Lean generation must remain usable in lightweight formal-tooling jobs.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any


_PUBLIC_OBJECTS: dict[str, tuple[str, str]] = {
    "CheckResult": ("fqv.results", "CheckResult"),
    "VerificationReport": (
        "fqv.results",
        "VerificationReport",
    ),
    "bell_contract": ("fqv.bell", "bell_contract"),
    "build_bell_circuit": (
        "fqv.bell",
        "build_bell_circuit",
    ),
    "build_bell_minus_circuit": (
        "fqv.bell",
        "build_bell_minus_circuit",
    ),
    "build_ghz3_circuit": (
        "fqv.ghz",
        "build_ghz3_circuit",
    ),
    "circuit_to_ir": ("fqv.ir", "circuit_to_ir"),
    "export_ir": ("fqv.ir", "export_ir"),
    "ghz3_contract": ("fqv.ghz", "ghz3_contract"),
    "verify_contract": ("fqv.checks", "verify_contract"),
    "TranspilationConfig": (
        "fqv.transpilation",
        "TranspilationConfig",
    ),
    "check_operator_equivalence": (
        "fqv.transpilation",
        "check_operator_equivalence",
    ),
    "transpile_and_check": (
        "fqv.transpilation",
        "transpile_and_check",
    ),
}

__all__ = sorted(_PUBLIC_OBJECTS)


def __getattr__(name: str) -> Any:
    """Load public objects only when callers actually request them."""

    try:
        module_name, object_name = _PUBLIC_OBJECTS[name]
    except KeyError as error:
        raise AttributeError(name) from error

    module = import_module(module_name)
    return getattr(module, object_name)
