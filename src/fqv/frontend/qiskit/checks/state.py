"""Exact ideal state checks."""

from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from fqv.domain.contracts import QuantumContract
from fqv.domain.reports import CheckResult, VerificationReport


def check_target_state(
    circuit: QuantumCircuit,
    contract: QuantumContract,
    report: VerificationReport,
) -> Statevector:
    """Evolve the declared input and verify the complete target state."""

    # Evolve the contract input explicitly. Relying on Qiskit's implicit
    # all-zero input would silently ignore an important contract precondition.
    actual = Statevector(
        np.asarray(contract.initial_state, dtype=complex)
    ).evolve(circuit)
    target = Statevector(
        np.asarray(contract.target_state, dtype=complex)
    )
    # Fidelity ignores global phase, and `equiv` independently confirms that
    # every amplitude agrees up to one common phase.
    overlap = np.vdot(target.data, actual.data)
    fidelity = float(abs(overlap) ** 2)
    phase_equivalent = bool(actual.equiv(target))
    report.add(
        CheckResult(
            name="target-state",
            passed=(
                fidelity >= contract.fidelity_threshold
                and phase_equivalent
            ),
            details=(
                f"fidelity={fidelity:.12f}, "
                f"equivalent-up-to-global-phase={phase_equivalent}"
            ),
            data={
                "fidelity": fidelity,
                "threshold": contract.fidelity_threshold,
                "equivalent_up_to_global_phase": phase_equivalent,
            },
        )
    )
    return actual
