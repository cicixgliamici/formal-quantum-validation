"""Transpile a Qiskit circuit and verify preservation of its full operator.

The verification CLI calls this optional pipeline after contract checks. It
calls Qiskit transpilation, compares source and result as operators, and
returns both objects to the CLI; the CLI then calls the Qiskit IR exporter.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Operator, process_fidelity

from fqv.domain.reports import EquivalenceReport
from fqv.domain.transpilation import TranspilationCertificate
from fqv.frontend.qiskit.extraction import circuit_to_ir
from fqv.ir.validation import check_ir
from fqv.pipeline.transpilation_certificate import certify_h_cancellations

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
    """Reproducible policy for one logical transpilation experiment.

    Qiskit's passes may contain stochastic choices, so the seed and pinned
    basis belong to the evidence rather than being incidental implementation
    settings. The default basis remains inside IR 0.1. Exact export additionally
    requires zero stored global phase and no attached layout.

    cli.main constructs this from command-line flags and passes it to
    transpile_and_check. That function uses the basis, optimization level,
    and seed to call Qiskit; check_operator_equivalence uses the threshold.
    The same settings are copied into EquivalenceReport for reproducibility.
    Currently 1 - equivalence_threshold also bounds the phase-aligned maximum
    entry error, so the threshold controls both numerical acceptance checks.
    """

    optimization_level: int = 1
    seed_transpiler: int = 7
    basis_gates: tuple[str, ...] = DEFAULT_BASIS_GATES
    equivalence_threshold: float = 1.0 - 1e-12

    def __post_init__(self) -> None:
        """Reject settings that would make reports ambiguous."""

        if (
            type(self.optimization_level) is not int
            or self.optimization_level not in range(4)
        ):
            raise ValueError(
                "optimization_level must be in [0, 3]"
            )
        if type(self.seed_transpiler) is not int or self.seed_transpiler < 0:
            raise ValueError(
                "seed_transpiler must be a non-negative integer"
            )
        if not self.basis_gates:
            raise ValueError("basis_gates cannot be empty")
        if not 0.0 <= self.equivalence_threshold <= 1.0:
            raise ValueError(
                "equivalence_threshold must be in [0, 1]"
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

    # A nonzero source entry gives a stable phase reference. Dividing two
    # entries near zero would amplify numerical noise, so those are excluded.
    # The largest entry is the most stable reference and argmax avoids an
    # additional array of coordinates proportional to the full operator size.
    row, column = np.unravel_index(np.argmax(np.abs(source)), source.shape)
    if abs(source[row, column]) <= tolerance:
        return float(np.max(np.abs(candidate - source)))

    ratio = candidate[row, column] / source[row, column]
    if abs(ratio) <= tolerance:
        # A missing pivot already witnesses disagreement for every phase.
        # Keep the diagnostic finite so it remains valid standard JSON.
        return float(np.max(np.abs(candidate - source)))

    # Only one common phase is unobservable. Relative phases remain visible in
    # the entry-wise error and therefore still cause verification to fail.
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


def transpile_check_and_certify(
    circuit: QuantumCircuit,
    *,
    config: TranspilationConfig | None = None,
) -> tuple[QuantumCircuit, EquivalenceReport, TranspilationCertificate]:
    """Run Qiskit and certify the result when it uses only known exact rules."""

    transpiled, report = transpile_and_check(circuit, config=config)
    if not report.passed:
        raise ValueError("cannot certify a failed executable equivalence check")

    # Export restrictions deliberately precede formal generation. In particular,
    # exact IR 0.1 cannot erase a stored global phase or a transpiler layout.
    source_ir = check_ir(circuit_to_ir(circuit))
    candidate_ir = check_ir(circuit_to_ir(transpiled))
    certificate = certify_h_cancellations(source_ir, candidate_ir)
    return transpiled, report, certificate
