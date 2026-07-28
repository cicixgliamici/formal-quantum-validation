from __future__ import annotations

from importlib.resources import as_file, files

from qiskit import QuantumCircuit

from fqv.contracts import QuantumContract, load_contract


def build_ghz_circuit(num_qubits: int) -> QuantumCircuit:
    """Prepare GHZ(n) with one Hadamard and a fan-out of CNOT gates."""

    if num_qubits < 1:
        raise ValueError("GHZ requires at least one qubit")

    circuit = QuantumCircuit(
        num_qubits,
        name=f"ghz{num_qubits}",
    )
    circuit.h(0)

    # Fan-out matches the circuit family used by the parametric Lean proof.
    for target in range(1, num_qubits):
        circuit.cx(0, target)

    return circuit


def build_ghz3_circuit() -> QuantumCircuit:
    """Prepare the fixed GHZ(3) regression circuit."""

    # Keep the original chain as an independent equivalent implementation.
    circuit = QuantumCircuit(3, name="ghz3")
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    return circuit


def ghz3_contract() -> QuantumContract:
    """Load the canonical shared GHZ(3) contract."""

    resource = files("fqv.data").joinpath(
        "ghz3.contract.json"
    )
    with as_file(resource) as contract_path:
        return load_contract(contract_path)
