from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
import json
from typing import Any

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Operator, process_fidelity


DEFAULT_BASIS_GATES = (
    "id",
    "x",
    "z",
    "h",
    "cx",
    "swap",
)


@dataclass(frozen=True)
class TranspilationConfig:
    """Deterministic configuration for logical-circuit transpilation."""

    optimization_level: int = 1
    seed_transpiler: int = 7
    basis_gates: tuple[str, ...] = DEFAULT_BASIS_GATES
    equivalence_threshold: float = 1.0 - 1e-12

    def __post_init__(self) -> None:
        """Reject settings that would make reports ambiguous."""

        if self.optimization_level not in range(4):
            raise ValueError(
                "optimization_level must be in [0, 3]"
            )
        if self.seed_transpiler < 0:
            raise ValueError(
                "seed_transpiler must be non-negative"
            )
        if not self.basis_gates:
            raise ValueError("basis_gates cannot be empty")
        if not 0.0 <= self.equivalence_threshold <= 1.0:
            raise ValueError(
                "equivalence_threshold must be in [0, 1]"
            )


@dataclass(frozen=True)
class EquivalenceReport:
    """Evidence that transpilation preserved the complete unitary."""

    passed: bool
    process_fidelity: float
    threshold: float
    equivalent_up_to_global_phase: bool
    max_phase_aligned_error: float
    source_depth: int
    transpiled_depth: int
    source_gate_counts: dict[str, int]
    transpiled_gate_counts: dict[str, int]
    optimization_level: int
    seed_transpiler: int
    basis_gates: tuple[str, ...]
    layout_applied: bool

    def to_dict(self) -> dict[str, Any]:
        """Return a stable JSON-compatible report."""

        return asdict(self)

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize the report for CI and experimental evidence."""

        return json.dumps(
            self.to_dict(),
            indent=indent,
            sort_keys=True,
        )

    def render_text(self) -> str:
        """Render the semantic result before optimization metrics."""

        result = "PASS" if self.passed else "FAIL"
        return "\n".join(
            [
                f"Transpilation equivalence: {result}",
                (
                    "Process fidelity: "
                    f"{self.process_fidelity:.15f}"
                ),
                (
                    "Equivalent up to global phase: "
                    f"{self.equivalent_up_to_global_phase}"
                ),
                (
                    "Maximum phase-aligned error: "
                    f"{self.max_phase_aligned_error:.3e}"
                ),
                (
                    f"Depth: {self.source_depth} -> "
                    f"{self.transpiled_depth}"
                ),
            ]
        )


def _plain_gate_counts(
    values: Mapping[object, object],
) -> dict[str, int]:
    """Normalize Qiskit count objects for deterministic reports."""

    return {
        str(gate): int(count)
        for gate, count in sorted(
            values.items(),
            key=lambda item: str(item[0]),
        )
    }


def _phase_aligned_error(
    source: np.ndarray,
    candidate: np.ndarray,
    *,
    tolerance: float,
) -> float:
    """Return maximum error after removing one unobservable global phase."""

    significant = np.argwhere(np.abs(source) > tolerance)
    if significant.size == 0:
        return float(np.max(np.abs(candidate - source)))

    row, column = significant[0]
    ratio = candidate[row, column] / source[row, column]
    if abs(ratio) <= tolerance:
        return float("inf")

    phase = ratio / abs(ratio)
    return float(
        np.max(np.abs(candidate - phase * source))
    )


def check_operator_equivalence(
    source: QuantumCircuit,
    candidate: QuantumCircuit,
    *,
    config: TranspilationConfig,
) -> EquivalenceReport:
    """Compare complete operators while respecting transpiler layouts."""

    if source.num_qubits != candidate.num_qubits:
        raise ValueError(
            "operator comparison requires equal qubit counts"
        )

    # `from_circuit` maps a transpiled circuit back through its stored layout.
    source_operator = Operator.from_circuit(source)
    candidate_operator = Operator.from_circuit(candidate)

    fidelity = float(
        np.real_if_close(
            process_fidelity(
                source_operator,
                candidate_operator,
                require_cp=True,
                require_tp=True,
            )
        )
    )
    error = _phase_aligned_error(
        source_operator.data,
        candidate_operator.data,
        tolerance=1e-14,
    )
    phase_equivalent = bool(
        error <= 1.0 - config.equivalence_threshold
    )
    passed = bool(
        fidelity >= config.equivalence_threshold
        and phase_equivalent
    )

    return EquivalenceReport(
        passed=passed,
        process_fidelity=fidelity,
        threshold=config.equivalence_threshold,
        equivalent_up_to_global_phase=phase_equivalent,
        max_phase_aligned_error=error,
        source_depth=source.depth(),
        transpiled_depth=candidate.depth(),
        source_gate_counts=_plain_gate_counts(
            source.count_ops()
        ),
        transpiled_gate_counts=_plain_gate_counts(
            candidate.count_ops()
        ),
        optimization_level=config.optimization_level,
        seed_transpiler=config.seed_transpiler,
        basis_gates=config.basis_gates,
        layout_applied=candidate.layout is not None,
    )


def transpile_and_check(
    circuit: QuantumCircuit,
    *,
    config: TranspilationConfig | None = None,
) -> tuple[QuantumCircuit, EquivalenceReport]:
    """Transpile deterministically and check semantic preservation."""

    selected_config = config or TranspilationConfig()
    transpiled = transpile(
        circuit,
        basis_gates=list(selected_config.basis_gates),
        optimization_level=(
            selected_config.optimization_level
        ),
        seed_transpiler=selected_config.seed_transpiler,
    )
    report = check_operator_equivalence(
        circuit,
        transpiled,
        config=selected_config,
    )
    return transpiled, report
