from __future__ import annotations

import json
from pathlib import Path

import pytest

from fqv.backend.lean.generator import generate_lean_module
from fqv.domain.contract_parser import contract_from_dict
from fqv.domain.contract_validation import InvalidContractError
from fqv.ir.validation import InvalidIrError, check_ir


PROJECT_ROOT = Path(__file__).parents[1]
CONTRACT_PATH = (
    PROJECT_ROOT
    / "src"
    / "fqv"
    / "data"
    / "bell.contract.json"
)
IR_PATH = PROJECT_ROOT / "examples" / "bell_ir.json"
GHZ_CONTRACT_PATH = (
    PROJECT_ROOT
    / "src"
    / "fqv"
    / "data"
    / "ghz3.contract.json"
)
GHZ_IR_PATH = PROJECT_ROOT / "examples" / "ghz3_ir.json"


def _load_object(path: Path) -> dict[str, object]:
    """Load a test fixture and assert that its root is an object."""

    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_shared_bell_contract_is_executable() -> None:
    contract = contract_from_dict(_load_object(CONTRACT_PATH))

    assert contract.num_qubits == 2
    assert contract.initial_state == (1.0, 0.0, 0.0, 0.0)
    assert abs(contract.target_state[0]) ** 2 == pytest.approx(0.5)


def test_contract_dimension_is_checked() -> None:
    data = _load_object(CONTRACT_PATH)
    data["target_state"] = ["one", "zero"]

    with pytest.raises(
        InvalidContractError,
        match="requires 4 amplitudes",
    ):
        contract_from_dict(data)


def test_contract_rejects_string_boolean() -> None:
    data = _load_object(CONTRACT_PATH)
    resources = data["resources"]
    assert isinstance(resources, dict)
    resources["allow_extra_gates"] = "false"

    with pytest.raises(
        InvalidContractError,
        match="must be a boolean",
    ):
        contract_from_dict(data)


def test_ir_rejects_equal_cnot_operands() -> None:
    ir = _load_object(IR_PATH)
    operations = ir["operations"]
    assert isinstance(operations, list)
    cnot = operations[1]
    assert isinstance(cnot, dict)
    cnot["targets"] = [0]

    with pytest.raises(
        InvalidIrError,
        match="same CNOT control and target",
    ):
        check_ir(ir)


def test_generator_rejects_dimension_mismatch() -> None:
    ir = _load_object(IR_PATH)
    contract = _load_object(CONTRACT_PATH)
    contract["qubits"] = 1
    contract["initial_state"] = ["one", "zero"]
    contract["target_state"] = ["one", "zero"]

    with pytest.raises(
        InvalidContractError,
        match="circuit has 2 qubits",
    ):
        generate_lean_module(ir, contract)


def test_bell_contract_generates_a_proof_obligation() -> None:
    module = generate_lean_module(
        _load_object(IR_PATH),
        _load_object(CONTRACT_PATH),
    )

    assert module.theorem_name == (
        "generatedBellStatePreparationCorrect"
    )
    assert "def generatedBellStatePreparationCircuit" in module.source
    assert "theorem generatedBellStatePreparationCorrect" in module.source
    assert "sorry" not in module.source


def test_ghz3_contract_generates_a_general_proof() -> None:
    module = generate_lean_module(
        _load_object(GHZ_IR_PATH),
        _load_object(GHZ_CONTRACT_PATH),
    )

    assert module.theorem_name == (
        "generatedGHZThreeQubitPreparationCorrect"
    )
    assert ": Circuit 3" in module.source
    assert ".cnot 1 2 (by decide)" in module.source
    assert "cases bit2 : basis 2" in module.source
