"""Pure domain representation of an ideal unitary circuit contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from fqv.domain.expectations import ProbabilityExpectation


@dataclass(frozen=True)
class QuantumContract:
    """Technology-independent specification of one circuit obligation.

    Instances represent data that already crossed the parsing boundary. The
    class deliberately contains no file paths, Qiskit objects, or Lean source:
    every frontend and backend must interpret the same domain contract instead
    of maintaining its own specification.

    `initial_state` and `target_state` follow Qiskit's little-endian amplitude
    order. Resource counts describe the logical source circuit, not a
    hardware-routed or transpiled implementation.
    """

    name: str
    num_qubits: int
    gate_counts: Mapping[str, int]
    allow_extra_gates: bool
    initial_state: Sequence[complex]
    target_state: Sequence[complex]
    fidelity_threshold: float
    probabilities: tuple[ProbabilityExpectation, ...]
