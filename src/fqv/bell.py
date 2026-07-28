"""Compatibility wrapper for Bell Qiskit fixtures."""

from fqv.frontend.qiskit.circuits import (
    bell_contract,
    build_bell_circuit,
    build_bell_minus_circuit,
)

__all__ = [
    "bell_contract",
    "build_bell_circuit",
    "build_bell_minus_circuit",
]
