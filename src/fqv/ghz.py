"""Compatibility wrapper for GHZ Qiskit fixtures."""

from fqv.frontend.qiskit.circuits import (
    build_ghz_circuit,
    build_ghz3_circuit,
    ghz3_contract,
)

__all__ = [
    "build_ghz_circuit",
    "build_ghz3_circuit",
    "ghz3_contract",
]
