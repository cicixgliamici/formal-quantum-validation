"""Reference Qiskit circuits and packaged contracts."""

from __future__ import annotations

from importlib.resources import as_file, files

from qiskit import QuantumCircuit

from fqv.domain.contract_parser import load_contract
from fqv.domain.contracts import QuantumContract


def build_bell_circuit() -> QuantumCircuit:
    """Build the reference circuit for the positive Bell-state contract."""

    circuit = QuantumCircuit(2, name="bell_phi_plus")
    circuit.h(0)
    circuit.cx(0, 1)
    return circuit


def build_bell_minus_circuit() -> QuantumCircuit:
    """Build a relative-phase mutation with unchanged basis probabilities."""

    circuit = build_bell_circuit()
    circuit.name = "bell_phi_minus"
    circuit.z(0)
    return circuit


def build_ghz_circuit(num_qubits: int) -> QuantumCircuit:
    """Build the fan-out GHZ family matched by the parametric Lean proof."""

    if num_qubits < 1:
        raise ValueError("GHZ requires at least one qubit")
    circuit = QuantumCircuit(num_qubits, name=f"ghz{num_qubits}")
    circuit.h(0)
    for target in range(1, num_qubits):
        circuit.cx(0, target)
    return circuit


def build_ghz3_circuit() -> QuantumCircuit:
    """Build the fixed CNOT-chain GHZ(3) regression circuit.

    The chain intentionally differs from the parametric fan-out constructor.
    Both prepare the same state, so keeping both exercises semantic checking
    rather than comparing identical source syntax.
    """

    circuit = QuantumCircuit(3, name="ghz3")
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    return circuit


def _packaged_contract(filename: str) -> QuantumContract:
    """Load a package resource without exposing resource paths to callers."""

    resource = files("fqv.data").joinpath(filename)
    with as_file(resource) as contract_path:
        return load_contract(contract_path)


def bell_contract() -> QuantumContract:
    """Return the canonical Bell contract shared by executable checks."""

    return _packaged_contract("bell.contract.json")


def ghz3_contract() -> QuantumContract:
    """Return the canonical fixed-size GHZ(3) contract."""

    return _packaged_contract("ghz3.contract.json")
