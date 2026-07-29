"""Cross-layer regression and mutation tests for the validation boundaries."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pytest
from qiskit.quantum_info import Operator, Statevector

from fqv.backend.lean.generator import generate_lean_module
from fqv.domain.contract_validation import InvalidContractError
from fqv.frontend.qiskit.circuits import (
    build_ghz_circuit,
    build_ghz3_circuit,
)
from fqv.frontend.qiskit.conversion import checked_ir_to_qiskit
from fqv.frontend.qiskit.extraction import circuit_to_ir
from fqv.ir.validation import InvalidIrError, check_ir


PROJECT_ROOT = Path(__file__).parents[1]
GHZ_IR_PATH = PROJECT_ROOT / "examples" / "ghz3_ir.json"
GHZ_CONTRACT_PATH = (
    PROJECT_ROOT / "src" / "fqv" / "data" / "ghz3.contract.json"
)


def _load_object(path: Path) -> dict[str, object]:
    """Return an independent mutable copy of one committed JSON fixture."""

    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


@pytest.mark.parametrize("num_qubits", range(1, 9))
def test_parametric_ghz_has_expected_fanout_structure(
    num_qubits: int,
) -> None:
    """Keep the Python constructor aligned with the circuit proved in Lean."""

    operations = circuit_to_ir(build_ghz_circuit(num_qubits))["operations"]

    assert operations[0] == {"gate": "H", "targets": [0]}
    assert operations[1:] == [
        {
            "gate": "CNOT",
            "controls": [0],
            "targets": [target],
        }
        for target in range(1, num_qubits)
    ]


@pytest.mark.parametrize("num_qubits", range(1, 9))
def test_parametric_ghz_has_only_two_normalized_branches(
    num_qubits: int,
) -> None:
    """Catch amplitude leakage, wrong targets, and normalization regressions."""

    state = Statevector.from_instruction(build_ghz_circuit(num_qubits)).data
    nonzero_indices = np.flatnonzero(np.abs(state) > 1e-12)

    assert nonzero_indices.tolist() == [0, (2**num_qubits) - 1]
    assert np.linalg.norm(state) == pytest.approx(1.0)
    assert state[0] == pytest.approx(1 / np.sqrt(2))
    assert state[-1] == pytest.approx(1 / np.sqrt(2))


def test_chain_and_fanout_ghz3_agree_only_on_the_intended_input() -> None:
    """Document why equal output states do not imply equal circuit operators."""

    chain = build_ghz3_circuit()
    fanout = build_ghz_circuit(3)

    assert Statevector.from_instruction(chain).equiv(
        Statevector.from_instruction(fanout)
    )
    assert not np.allclose(
        Operator(chain).data,
        Operator(fanout).data,
    )


def test_every_ir_gate_round_trips_without_reordering() -> None:
    """Exercise the complete IR 0.1 gate vocabulary through Qiskit."""

    raw = {
        "schema_version": "0.1",
        "name": "all_supported_gates",
        "qubits": 3,
        "operations": [
            {"gate": "I", "targets": [2]},
            {"gate": "X", "targets": [0]},
            {"gate": "Z", "targets": [1]},
            {"gate": "H", "targets": [2]},
            {"gate": "CNOT", "controls": [2], "targets": [0]},
            {"gate": "SWAP", "targets": [0, 1]},
        ],
    }

    reconstructed = checked_ir_to_qiskit(check_ir(raw))

    assert circuit_to_ir(reconstructed) == raw


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ({"schema_version": "9.9"}, "schema version"),
        ({"name": ""}, "non-empty string"),
        ({"qubits": True}, "positive integer"),
        ({"qubits": 0}, "positive integer"),
        ({"operations": "H(0)"}, "JSON array"),
    ],
)
def test_ir_rejects_malformed_document_roots(
    mutation: dict[str, object],
    message: str,
) -> None:
    """Reject malformed metadata before any provider receives the document."""

    raw = _load_object(GHZ_IR_PATH)
    raw.update(mutation)

    with pytest.raises(InvalidIrError, match=message):
        check_ir(raw)


@pytest.mark.parametrize(
    ("operation", "message"),
    [
        (None, "must be a JSON object"),
        ({"gate": "RX", "targets": [0]}, "unsupported gate"),
        ({"gate": "H", "targets": []}, "must contain 1"),
        ({"gate": "X", "targets": [3]}, r"index in \[0, 3\)"),
        (
            {"gate": "CNOT", "controls": [1], "targets": [1]},
            "same CNOT control and target",
        ),
        (
            {"gate": "SWAP", "targets": [2, 2]},
            "same SWAP target twice",
        ),
    ],
)
def test_ir_rejects_malformed_operations(
    operation: object,
    message: str,
) -> None:
    """Mutation-test every gate-specific structural safety boundary."""

    raw = _load_object(GHZ_IR_PATH)
    raw["operations"] = [operation]

    with pytest.raises(InvalidIrError, match=message):
        check_ir(raw)


def test_lean_generation_is_deterministic_and_side_effect_free() -> None:
    """The same evidence must always produce byte-identical Lean source."""

    ir = _load_object(GHZ_IR_PATH)
    contract = _load_object(GHZ_CONTRACT_PATH)
    original_ir = copy.deepcopy(ir)
    original_contract = copy.deepcopy(contract)

    first = generate_lean_module(ir, contract)
    second = generate_lean_module(ir, contract)

    assert first == second
    assert ir == original_ir
    assert contract == original_contract


def test_lean_path_rejects_unsupported_exact_amplitudes() -> None:
    """Reject approximate tokens at the shared contract parsing boundary."""

    contract = _load_object(GHZ_CONTRACT_PATH)
    target_state = contract["target_state"]
    assert isinstance(target_state, list)
    target_state[0] = "0.70710678118"

    with pytest.raises(
        InvalidContractError,
        match=r"target_state\[0\] uses unsupported amplitude",
    ):
        generate_lean_module(_load_object(GHZ_IR_PATH), contract)
