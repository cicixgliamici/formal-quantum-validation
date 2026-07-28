"""Logical resource and gate-inventory checks."""

from __future__ import annotations

from qiskit import QuantumCircuit

from fqv.domain.contracts import QuantumContract
from fqv.domain.reports import CheckResult, VerificationReport


def _plain_counts(values: object) -> dict[str, int]:
    """Normalize Qiskit count-like mappings."""

    return {
        str(key): int(value)
        for key, value in values.items()
    }


def check_structure(
    circuit: QuantumCircuit,
    contract: QuantumContract,
    report: VerificationReport,
) -> None:
    """Check qubit count, declared gate counts, and unexpected gates."""

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
    # Qiskit count keys are provider objects; reports use stable plain strings.
    observed_counts = _plain_counts(circuit.count_ops())
    for gate_name, expected_count in contract.gate_counts.items():
        observed_count = observed_counts.get(gate_name, 0)
        report.add(
            CheckResult(
                name=f"gate-count:{gate_name}",
                passed=observed_count == expected_count,
                details=(
                    f"expected {expected_count}, observed {observed_count}"
                ),
                data={
                    "gate": gate_name,
                    "expected": expected_count,
                    "observed": observed_count,
                },
            )
        )
    # Extra gates are checked separately from expected counts so diagnostics
    # distinguish a missing required gate from an undeclared additional gate.
    if not contract.allow_extra_gates:
        unexpected = sorted(
            set(observed_counts) - set(contract.gate_counts)
        )
        report.add(
            CheckResult(
                name="unexpected-gates",
                passed=not unexpected,
                details="none" if not unexpected else f"found {unexpected}",
                data={"unexpected": unexpected},
            )
        )
