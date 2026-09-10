"""Exact ideal state checks."""

from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from fqv.domain.contract_validation import InvalidContractError
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
    initial = Statevector(
        np.asarray(contract.initial_state, dtype=complex)
    )
    target = Statevector(
        np.asarray(contract.target_state, dtype=complex)
    )
    # Public Python callers can construct contracts without the JSON parser.
    # Check normalization here too, before computing fidelity or sampling.
    for name, state in (("initial_state", initial), ("target_state", target)):
        norm_squared = float(np.vdot(state.data, state.data).real)
        if not np.isclose(norm_squared, 1.0, rtol=0.0, atol=1e-12):
            raise InvalidContractError(f"{name} must be normalized")
    actual = initial.evolve(circuit)
    # Lean proves exact vector equality. Numerical evidence uses a fixed
    # roundoff allowance, but must not erase global phase from the contract.
    overlap = np.vdot(target.data, actual.data)
    fidelity = float(np.clip(abs(overlap) ** 2, 0.0, 1.0))
    phase_equivalent = bool(actual.equiv(target))
    amplitude_error = float(np.max(np.abs(actual.data - target.data)))
    amplitudes_match = amplitude_error <= 1e-12
    report.add(
        CheckResult(
            name="target-state",
            passed=(
                fidelity >= contract.fidelity_threshold
                and amplitudes_match
            ),
            details=(
                f"fidelity={fidelity:.12f}, "
                f"amplitudes-match={amplitudes_match}, "
                f"max-amplitude-error={amplitude_error:.3g}"
            ),
            data={
                "fidelity": fidelity,
                "threshold": contract.fidelity_threshold,
                "equivalent_up_to_global_phase": phase_equivalent,
                "amplitudes_match": amplitudes_match,
                "max_amplitude_error": amplitude_error,
                "amplitude_tolerance": 1e-12,
            },
        )
    )
    return actual
