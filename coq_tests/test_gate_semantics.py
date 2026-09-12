"""Check all six public gates against independent computational-basis rules.

The reference uses bit operations and exact amplitude tokens, never SQIR's
lowering or the production matrix implementation. This finite regression covers
every placement and basis input through three qubits. Hadamard and SWAP are
capped at two because the pinned matrix tactic cannot reliably reduce their
dimension-eight proof terms within the CI timeout.
"""

from itertools import permutations
from pathlib import Path

import pytest

from fqv.backend.coq.generator import generate_coq_module

GATES = ("I", "X", "Z", "H", "CNOT", "SWAP")
COQ_IMPORT = "From QuantumValidation Require Import Circuit.\n"
# Eight cases amortize coqc startup without creating timeout-prone giant terms.
CASES_PER_MODULE = 8


def basis_state(num_qubits: int, index: int, token: str = "one") -> list[str]:
    """Return one exact computational-basis state in IR amplitude order."""

    state = ["zero"] * (1 << num_qubits)
    state[index] = token
    return state


def expected_state(
    gate: str, operands: tuple[int, ...], basis: int, dim: int,
) -> list[str]:
    """Implement the textbook basis action without calling production semantics.

    Integer bit `k` represents qubit `k`, matching the shared IR. Keeping this
    oracle as bit manipulation prevents an SQIR lowering bug from being copied
    into both the implementation and its expected value.
    """
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
    """Build the smallest raw IR operation accepted by the production checker."""

    if gate == "CNOT":
        return {"gate": gate, "controls": [operands[0]], "targets": [operands[1]]}
    return {"gate": gate, "targets": list(operands)}


def obligation(
    dim: int, operations: list[dict], initial: list[str], target: list[str],
) -> str:
    """Turn one independent basis expectation into a generated Coq theorem."""

    ir = {"schema_version": "0.1", "name": "basis_regression",
          "qubits": dim, "operations": operations}
    contract = {
        "schema_version": "0.1", "name": "Basis regression", "qubits": dim,
        "initial_state": initial, "target_state": target,
        "fidelity_threshold": 1.0, "probabilities": [],
        "resources": {"gate_counts": {}, "allow_extra_gates": True},
    }
    source = generate_coq_module(ir, contract).source
    if dim == 3:
        # Production artifacts retain solve_circuit. Concrete 8x8 regressions
        # use the dedicated solver so false DJ mutations still fail promptly.
        source = source.replace("  solve_circuit.", "  solve_basis_circuit.")
    return source


def compile_cases(sources: list[str], destination: Path, coq_compile) -> None:
    """Compile bounded batches so matrix reduction stays below the CI timeout."""

    # Require belongs at file scope; modules isolate production theorem names.
    assert all(source.startswith(COQ_IMPORT) for source in sources)
    for batch_start in range(0, len(sources), CASES_PER_MODULE):
        # Each Coq Module scopes repeated generated names such as
        # basis_regression_correct without editing production generator output.
        batch = sources[batch_start:batch_start + CASES_PER_MODULE]
        source = COQ_IMPORT + "\n".join(
            f"Module Case{index}.\n{case.removeprefix(COQ_IMPORT)}\nEnd Case{index}."
            for index, case in enumerate(batch, start=batch_start)
        )
        batch_destination = destination.with_stem(
            f"{destination.stem}_{batch_start // CASES_PER_MODULE}"
        )
        result = coq_compile(source, batch_destination)
        assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("gate,dim", [
    (gate, dim) for gate in GATES for dim in (1, 2, 3)
    # Binary gates have no valid placement in a one-qubit register.
    if dim > 1 or gate not in {"CNOT", "SWAP"}
    # These caps describe pinned tactic performance, not the public IR limits.
    if dim < 3 or gate not in {"H", "SWAP"}
])
def test_every_gate_placement_and_basis(gate: str, dim: int, tmp_path: Path, coq_compile):
    """Check every valid placement and basis input for one gate and dimension."""

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
    """Ensure the empty source list lowers to SQIR SKIP and preserves every basis."""

    sources = [obligation(dim, [], basis_state(dim, basis), basis_state(dim, basis))
               for basis in range(1 << dim)]
    compile_cases(sources, tmp_path / "Empty.v", coq_compile)


def test_exact_signed_and_imaginary_inputs(tmp_path: Path, coq_compile):
    """Exercise exact Coq serialization beyond unsigned real basis states."""

    # Basis gate cases exercise real signs; these also check complex serialization.
    sources = [
        obligation(1, [operation("I", (0,))], basis_state(1, 1, token),
                   basis_state(1, 1, token))
        for token in ("minus_one", "i", "minus_i")
    ]
    compile_cases(sources, tmp_path / "ComplexInputs.v", coq_compile)
