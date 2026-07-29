"""Compose independent Qiskit checks for one domain contract.

Called by ``pipeline.verify`` after the CLI has built a Qiskit circuit and a
validated domain contract. This module calls the structure, state, exact
probability, and sampled-probability checks in dependency order, then returns
their shared report to the pipeline.
"""

from __future__ import annotations

from qiskit import QuantumCircuit

from fqv.domain.contracts import QuantumContract
from fqv.domain.reports import VerificationReport
from fqv.frontend.qiskit.checks import (
    check_exact_probabilities,
    check_sampled_probabilities,
    check_structure,
    check_target_state,
)


def verify_contract(
    circuit: QuantumCircuit,
    contract: QuantumContract,
    *,
    shots: int = 4096,
    seed: int = 7,
) -> VerificationReport:
    """Run all executable checks supported by the Qiskit frontend."""

    if shots <= 0:
        raise ValueError("shots must be strictly positive")

    report = VerificationReport(contract_name=contract.name)
    # Structure must be checked before simulation. The state check then
    # produces the Statevector consumed by both probability checks.
    check_structure(circuit, contract, report)
    state = check_target_state(circuit, contract, report)
    check_exact_probabilities(state, contract, report)
    check_sampled_probabilities(
        state,
        contract,
        report,
        shots=shots,
        seed=seed,
    )
    return report
