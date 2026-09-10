"""Check all six public gates against independent computational-basis rules.

The reference uses bit operations and exact amplitude tokens, never SQIR's
lowering or the production matrix implementation. This finite regression
covers every placement and basis input on one-, two-, and three-qubit registers.
"""

from itertools import permutations
from pathlib import Path

import pytest

from fqv.backend.coq.generator import generate_coq_module


GATES = ("I", "X", "Z", "H", "CNOT", "SWAP")
COQ_IMPORT = "From QuantumValidation Require Import Circuit.\n"


def basis_state(num_qubits: int, index: int, token: str = "one") -> list[str]:
    state = ["zero"] * (1 << num_qubits)
    state[index] = token
    return state


def expected_state(gate: str, operands: tuple[int, ...], basis: int, dim: int):
    """Implement the textbook basis action in the IR's little-endian order."""
    first = operands[0]
    bit = (basis >> first) & 1
    if gate == "H":
        state = basis_state(dim, basis & ~(1 << first), "inv_sqrt_two")
        state[basis | (1 << first)] = "minus_inv_sqrt_two" if bit else "inv_sqrt_two"
        return state
    if gate == "Z":
        return basis_state(dim, basis, "minus_one" if bit else "one")
    if gate == "X":
        basis ^= 1 << first
    if gate == "CNOT" and bit:
        basis ^= 1 << operands[1]
    if gate == "SWAP" and bit != ((basis >> operands[1]) & 1):
        basis ^= (1 << first) | (1 << operands[1])
    return basis_state(dim, basis)


def operation(gate: str, operands: tuple[int, ...]) -> dict:
    if gate == "CNOT":
        return {"gate": gate, "controls": [operands[0]], "targets": [operands[1]]}
    return {"gate": gate, "targets": list(operands)}


def obligation(dim: int, operations: list[dict], initial: list[str], target: list[str]):
    ir = {"schema_version": "0.1", "name": "basis_regression",
          "qubits": dim, "operations": operations}
    contract = {
        "schema_version": "0.1", "name": "Basis regression", "qubits": dim,
        "initial_state": initial, "target_state": target,
        "fidelity_threshold": 1.0, "probabilities": [],
        "resources": {"gate_counts": {}, "allow_extra_gates": True},
    }
    return generate_coq_module(ir, contract).source


def compile_cases(sources: list[str], destination: Path, coq_compile) -> None:
    # Require belongs at file scope; modules isolate production theorem names.
    assert all(source.startswith(COQ_IMPORT) for source in sources)
    source = COQ_IMPORT + "\n".join(
        f"Module Case{index}.\n{source.removeprefix(COQ_IMPORT)}\nEnd Case{index}."
        for index, source in enumerate(sources)
    )
    result = coq_compile(source, destination)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("gate,dim", [
    (gate, dim) for gate in GATES for dim in (1, 2, 3)
    if dim > 1 or gate not in {"CNOT", "SWAP"}
])
def test_every_gate_placement_and_basis(gate: str, dim: int, tmp_path: Path, coq_compile):
    width = 2 if gate in {"CNOT", "SWAP"} else 1
    sources = [
        obligation(dim, [operation(gate, operands)], basis_state(dim, basis),
                   expected_state(gate, operands, basis, dim))
        for operands in permutations(range(dim), width)
        for basis in range(1 << dim)
    ]
    # Both operand orders and non-adjacent placements are required coverage.
    assert len(sources) == dim * (dim - 1 if width == 2 else 1) * (1 << dim)
    compile_cases(sources, tmp_path / "GateCases.v", coq_compile)


@pytest.mark.parametrize("dim", [1, 2, 3])
def test_empty_circuit_is_identity(dim: int, tmp_path: Path, coq_compile):
    sources = [obligation(dim, [], basis_state(dim, basis), basis_state(dim, basis))
               for basis in range(1 << dim)]
    compile_cases(sources, tmp_path / "Empty.v", coq_compile)


def test_exact_signed_and_imaginary_inputs(tmp_path: Path, coq_compile):
    # Basis gate cases exercise real signs; these also check complex serialization.
    sources = [
        obligation(1, [operation("I", (0,))], basis_state(1, 1, token),
                   basis_state(1, 1, token))
        for token in ("minus_one", "i", "minus_i")
    ]
    compile_cases(sources, tmp_path / "ComplexInputs.v", coq_compile)
