from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class ProbabilityExpectation:
    """Expected probability for one computational-basis outcome."""

    outcome: str
    expected: float

    # Exact statevector verification tolerance.
    exact_tolerance: float = 1e-12

    # Empirical sampling tolerance.
    sampled_tolerance: float = 0.05


@dataclass(frozen=True)
class QuantumContract:
    """Restricted contract for an ideal unitary quantum circuit."""

    name: str

    # Structural specification.
    num_qubits: int
    gate_counts: Mapping[str, int]
    allow_extra_gates: bool

    # Semantic specification.
    target_state: Sequence[complex]
    fidelity_threshold: float

    # Measurement specification.
    probabilities: tuple[ProbabilityExpectation, ...]
