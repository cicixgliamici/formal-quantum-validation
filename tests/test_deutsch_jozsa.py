"""Tests for 2-bit Deutsch-Jozsa circuits, contracts, and dual formal backends."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from qiskit.quantum_info import Statevector

from fqv.backend.coq.generator import generate_coq_module, write_coq_module
from fqv.backend.lean.generator import generate_lean_module, write_lean_module
from fqv.frontend.qiskit.circuits import (
    build_dj2_balanced_circuit,
    build_dj2_constant_circuit,
    dj2_balanced_contract,
    dj2_constant_contract,
)
from fqv.frontend.qiskit.conversion import checked_ir_to_qiskit
from fqv.frontend.qiskit.extraction import circuit_to_ir
from fqv.frontend.qiskit.verification import verify_contract
from fqv.ir.raw import load_raw_ir
from fqv.ir.validation import check_ir


PROJECT_ROOT = Path(__file__).parents[1]
EXAMPLES_DIR = PROJECT_ROOT / "examples"
DATA_DIR = PROJECT_ROOT / "src" / "fqv" / "data"


def test_dj2_constant_qiskit_circuit_and_contract() -> None:
    """Validate Qiskit execution for the constant oracle against the contract."""

    circuit = build_dj2_constant_circuit()
    contract = dj2_constant_contract()
    report = verify_contract(circuit, contract, shots=4096, seed=42)
    assert report.passed


def test_dj2_balanced_qiskit_circuit_and_contract() -> None:
    """Validate Qiskit execution for the balanced oracle against the contract."""

    circuit = build_dj2_balanced_circuit()
    contract = dj2_balanced_contract()
    report = verify_contract(circuit, contract, shots=4096, seed=42)
    assert report.passed


def test_dj2_ir_json_files_are_valid() -> None:
    """Verify that committed IR files match the checked domain representation."""

    for filename in ("dj2_constant_ir.json", "dj2_balanced_ir.json"):
        ir_path = EXAMPLES_DIR / filename
        assert ir_path.exists(), f"Missing {filename}"
        raw_ir = load_raw_ir(ir_path)
        checked_ir = check_ir(raw_ir)
        assert checked_ir.num_qubits == 3
        assert len(checked_ir.operations) > 0


def test_dj2_contract_json_files_are_valid() -> None:
    """Verify that committed contract files parse and have normalized states."""

    for filename in ("dj2_constant.contract.json", "dj2_balanced.contract.json"):
        contract_path = DATA_DIR / filename
        assert contract_path.exists(), f"Missing {filename}"
        contract_data = json.loads(contract_path.read_text(encoding="utf-8"))
        assert contract_data["qubits"] == 3
        assert contract_data["schema_version"] == "0.1"


def test_dj2_coq_generator_produces_valid_structure(tmp_path: Path) -> None:
    """Verify that generate_coq_module produces the expected SQIR theorems."""

    ir_path = EXAMPLES_DIR / "dj2_constant_ir.json"
    contract_path = DATA_DIR / "dj2_constant.contract.json"
    raw_ir = load_raw_ir(ir_path)
    contract_data = json.loads(contract_path.read_text(encoding="utf-8"))

    module = generate_coq_module(raw_ir, contract_data)
    assert "From QuantumLib Require Import Complex Dirac." in module.source
    assert "From SQIR Require Import UnitarySem." in module.source
    assert "deutsch_jozsa_two_bit_constant_circuit : base_ucom 3 :=" in module.source
    assert "Theorem deutsch_jozsa_two_bit_constant_correct :" in module.source
    assert "solve_matrix." in module.source

    out_file = tmp_path / "GeneratedDj2Constant.v"
    written = write_coq_module(raw_ir, contract_data, out_file)
    assert written == out_file
    assert written.read_text(encoding="utf-8") == module.source


def test_dj2_coq_generator_balanced(tmp_path: Path) -> None:
    """Verify Coq generation for the balanced Deutsch-Jozsa circuit."""

    ir_path = EXAMPLES_DIR / "dj2_balanced_ir.json"
    contract_path = DATA_DIR / "dj2_balanced.contract.json"
    raw_ir = load_raw_ir(ir_path)
    contract_data = json.loads(contract_path.read_text(encoding="utf-8"))

    module = generate_coq_module(raw_ir, contract_data)
    assert "CNOT 0 2" in module.source
    assert "deutsch_jozsa_two_bit_balanced_circuit : base_ucom 3 :=" in module.source
    assert "Theorem deutsch_jozsa_two_bit_balanced_correct :" in module.source


def test_coq_generator_bell_and_ghz3() -> None:
    """Verify Coq generation for the existing Bell and GHZ3 benchmarks."""

    bell_ir = load_raw_ir(EXAMPLES_DIR / "bell_ir.json")
    bell_contract = json.loads((DATA_DIR / "bell.contract.json").read_text(encoding="utf-8"))
    bell_mod = generate_coq_module(bell_ir, bell_contract)
    assert "bell_state_preparation_circuit : base_ucom 2 :=" in bell_mod.source
    assert "H 0 ;; CNOT 0 1" in bell_mod.source
    assert "Theorem bell_state_preparation_correct :" in bell_mod.source

    ghz_ir = load_raw_ir(EXAMPLES_DIR / "ghz3_ir.json")
    ghz_contract = json.loads((DATA_DIR / "ghz3.contract.json").read_text(encoding="utf-8"))
    ghz_mod = generate_coq_module(ghz_ir, ghz_contract)
    assert "ghz_three_qubit_preparation_circuit : base_ucom 3 :=" in ghz_mod.source
    assert "H 0 ;; CNOT 0 1 ;; CNOT 1 2" in ghz_mod.source
