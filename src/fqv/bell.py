from __future__ import annotations

from importlib.resources import as_file, files

from qiskit import QuantumCircuit

from fqv.contracts import QuantumContract, load_contract


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
    """Load the canonical shared Bell contract distributed with the package."""

    resource = files("fqv.data").joinpath(
        "bell.contract.json"
    )
    with as_file(resource) as contract_path:
        return load_contract(contract_path)
