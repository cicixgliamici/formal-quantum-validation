from __future__ import annotations

from importlib.resources import as_file, files

from qiskit import QuantumCircuit

from fqv.contracts import QuantumContract, load_contract


def build_ghz3_circuit() -> QuantumCircuit:
    """Prepare the three-qubit GHZ state."""

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
