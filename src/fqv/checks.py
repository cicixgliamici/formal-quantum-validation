from __future__ import annotations

from collections.abc import Mapping

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from fqv.contracts import QuantumContract
from fqv.results import CheckResult, VerificationReport


def _to_plain_count_dict(
    values: Mapping[object, object],
) -> dict[str, int]:
    """Convert Qiskit count-like objects to a plain dictionary."""

    return {
        str(key): int(value)
        for key, value in values.items()
    }


def _check_structure(
    circuit: QuantumCircuit,
    contract: QuantumContract,
    report: VerificationReport,
) -> None:
    """Check qubit count and gate inventory."""

    report.add(
        CheckResult(
            name="qubit-count",
            passed=circuit.num_qubits == contract.num_qubits,
            details=(
                f"expected {contract.num_qubits}, "
                f"observed {circuit.num_qubits}"
            ),
            data={
                "expected": contract.num_qubits,
                "observed": circuit.num_qubits,
            },
        )
    )

    observed_counts = _to_plain_count_dict(
        circuit.count_ops()
    )

    for gate_name, expected_count in contract.gate_counts.items():
        observed_count = observed_counts.get(gate_name, 0)

        report.add(
            CheckResult(
                name=f"gate-count:{gate_name}",
                passed=observed_count == expected_count,
                details=(
                    f"expected {expected_count}, "
                    f"observed {observed_count}"
                ),
                data={
                    "gate": gate_name,
                    "expected": expected_count,
                    "observed": observed_count,
                },
            )
        )

    if not contract.allow_extra_gates:
        expected_gate_names = set(contract.gate_counts)
        observed_gate_names = set(observed_counts)

        unexpected = sorted(
            observed_gate_names - expected_gate_names
        )

        report.add(
            CheckResult(
                name="unexpected-gates",
                passed=not unexpected,
                details=(
                    "none"
                    if not unexpected
                    else f"found {unexpected}"
                ),
                data={
                    "unexpected": unexpected,
                },
            )
        )


def _check_target_state(
    circuit: QuantumCircuit,
    contract: QuantumContract,
    report: VerificationReport,
) -> Statevector:
    """Verify the exact ideal output state."""

    actual_state = Statevector.from_instruction(circuit)

    target_state = Statevector(
        np.asarray(
            contract.target_state,
            dtype=complex,
        )
    )

    overlap = np.vdot(
        target_state.data,
        actual_state.data,
    )

    fidelity = float(abs(overlap) ** 2)

    equivalent_up_to_global_phase = bool(
        actual_state.equiv(target_state)
    )

    report.add(
        CheckResult(
            name="target-state",
            passed=(
                fidelity >= contract.fidelity_threshold
                and equivalent_up_to_global_phase
            ),
            details=(
                f"fidelity={fidelity:.12f}, "
                f"equivalent-up-to-global-phase="
                f"{equivalent_up_to_global_phase}"
            ),
            data={
                "fidelity": fidelity,
                "threshold": contract.fidelity_threshold,
                "equivalent_up_to_global_phase":
                    equivalent_up_to_global_phase,
            },
        )
    )

    return actual_state


def _check_exact_probabilities(
    state: Statevector,
    contract: QuantumContract,
    report: VerificationReport,
) -> None:
    """Check exact computational-basis probabilities."""

    probabilities = {
        str(outcome): float(probability)
        for outcome, probability
        in state.probabilities_dict().items()
    }

    for expectation in contract.probabilities:
        observed = probabilities.get(
            expectation.outcome,
            0.0,
        )

        difference = abs(
            observed - expectation.expected
        )

        report.add(
            CheckResult(
                name=(
                    f"exact-probability:"
                    f"{expectation.outcome}"
                ),
                passed=(
                    difference
                    <= expectation.exact_tolerance
                ),
                details=(
                    f"expected {expectation.expected:.6f}, "
                    f"observed {observed:.6f}"
                ),
                data={
                    "outcome": expectation.outcome,
                    "expected": expectation.expected,
                    "observed": observed,
                    "difference": difference,
                    "tolerance":
                        expectation.exact_tolerance,
                },
            )
        )


def _check_sampled_probabilities(
    state: Statevector,
    contract: QuantumContract,
    report: VerificationReport,
    *,
    shots: int,
    seed: int,
) -> None:
    """Check empirical computational-basis frequencies."""

    state.seed(seed)

    sampled_counts = _to_plain_count_dict(
        state.sample_counts(shots)
    )

    for expectation in contract.probabilities:
        observed_count = sampled_counts.get(
            expectation.outcome,
            0,
        )

        observed_frequency = observed_count / shots

        difference = abs(
            observed_frequency - expectation.expected
        )

        report.add(
            CheckResult(
                name=(
                    f"sampled-probability:"
                    f"{expectation.outcome}"
                ),
                passed=(
                    difference
                    <= expectation.sampled_tolerance
                ),
                details=(
                    f"expected {expectation.expected:.3f}, "
                    f"observed {observed_frequency:.3f} "
                    f"({observed_count}/{shots})"
                ),
                data={
                    "outcome": expectation.outcome,
                    "expected": expectation.expected,
                    "observed": observed_frequency,
                    "count": observed_count,
                    "shots": shots,
                    "seed": seed,
                    "difference": difference,
                    "tolerance":
                        expectation.sampled_tolerance,
                },
            )
        )


def verify_contract(
    circuit: QuantumCircuit,
    contract: QuantumContract,
    *,
    shots: int = 4096,
    seed: int = 7,
) -> VerificationReport:
    """Verify the Bell contract at multiple assurance levels.

    MVP 0 supports unitary circuits without measurement,
    reset or classical control.
    """

    if shots <= 0:
        raise ValueError(
            "shots must be strictly positive"
        )

    report = VerificationReport(
        contract_name=contract.name
    )

    _check_structure(
        circuit,
        contract,
        report,
    )

    state = _check_target_state(
        circuit,
        contract,
        report,
    )

    _check_exact_probabilities(
        state,
        contract,
        report,
    )

    _check_sampled_probabilities(
        state,
        contract,
        report,
        shots=shots,
        seed=seed,
    )

    return report
