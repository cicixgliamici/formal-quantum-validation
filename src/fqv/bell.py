from __future__ import annotations

from math import sqrt

from qiskit import QuantumCircuit

from fqv.contracts import ProbabilityExpectation, QuantumContract


def build_bell_circuit() -> QuantumCircuit:
    """Prepare |Φ+> = (|00> + |11>) / sqrt(2)."""

    circuit = QuantumCircuit(2, name="bell_phi_plus")

    circuit.h(0)
    circuit.cx(0, 1)

    return circuit


def build_bell_minus_circuit() -> QuantumCircuit:
    """Prepare |Φ-> = (|00> - |11>) / sqrt(2).

    This state has the same computational-basis probabilities as |Φ+>,
    but a different relative phase.
    """

    circuit = build_bell_circuit()
    circuit.name = "bell_phi_minus"

    circuit.z(0)

    return circuit


def bell_contract() -> QuantumContract:
    """Return the contract for Bell-state preparation."""

    amplitude = 1.0 / sqrt(2.0)

    return QuantumContract(
        name="Bell-state preparation",

        num_qubits=2,

        gate_counts={
            "h": 1,
            "cx": 1,
        },

        allow_extra_gates=False,

        # Qiskit ordering:
        # |00>, |01>, |10>, |11>
        target_state=(
            amplitude,
            0.0,
            0.0,
            amplitude,
        ),

        fidelity_threshold=1.0 - 1e-12,

        probabilities=(
            ProbabilityExpectation(
                outcome="00",
                expected=0.5,
            ),
            ProbabilityExpectation(
                outcome="01",
                expected=0.0,
            ),
            ProbabilityExpectation(
                outcome="10",
                expected=0.0,
            ),
            ProbabilityExpectation(
                outcome="11",
                expected=0.5,
            ),
        ),
    )
