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

    if type(shots) is not int or shots <= 0:
        raise ValueError("shots must be a strictly positive integer")
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    # Library callers need the same early dimension diagnostic as CLI callers.
    if circuit.num_qubits != contract.num_qubits:
        raise ValueError("circuit and contract must have the same qubit count")

    report = VerificationReport(contract_name=contract.name)
    # All checks append to the same report. A failed gate-count check does not
    # stop simulation: later checks still provide useful diagnostics. Invalid
    # input data, such as an unnormalized state, raises instead of returning a
    # completed report. The state is evolved once and reused by both probability
    # checks; the sampled check samples that ideal vector, not a physical device.
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
