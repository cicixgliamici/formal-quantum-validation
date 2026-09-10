"""Tests for 2-bit Deutsch-Jozsa circuits, contracts, and dual formal backends."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from qiskit.quantum_info import Statevector

from fqv.backend.coq.generator import (
    _format_state,
    generate_coq_module,
    write_coq_module,
)
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
    """Check serialization through Circuit.v; coq_tests checks proof acceptance."""

    ir_path = EXAMPLES_DIR / "dj2_constant_ir.json"
    contract_path = DATA_DIR / "dj2_constant.contract.json"
    raw_ir = load_raw_ir(ir_path)
    contract_data = json.loads(contract_path.read_text(encoding="utf-8"))

    module = generate_coq_module(raw_ir, contract_data)
    assert "From QuantumValidation Require Import Circuit." in module.source
    assert "Import QuantumValidationSQIR." in module.source
    assert "deutsch_jozsa_two_bit_constant_circuit : Circuit 3 :=" in module.source
    assert "GateX 2 :: GateH 0 :: GateH 1 :: GateH 2 :: GateH 0 :: GateH 1 :: nil" in module.source
    # Verify SQIR endianness: qubit 2 is the 3rd Dirac component ∣q0, q1, q2⟩
    assert "(/√2)%R .* ∣0, 0, 0⟩ .+ (- /√2)%R .* ∣0, 0, 1⟩" in module.source
    assert "Theorem deutsch_jozsa_two_bit_constant_correct :" in module.source
    assert "solve_circuit." in module.source

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
    assert "GateCNOT 0 2" in module.source
    assert "deutsch_jozsa_two_bit_balanced_circuit : Circuit 3 :=" in module.source
    # Verify SQIR endianness: query qubit 0 is 1, qubit 1 is 0, ancilla qubit 2 is 0 or 1
    assert "(/√2)%R .* ∣1, 0, 0⟩ .+ (- /√2)%R .* ∣1, 0, 1⟩" in module.source
    assert "Theorem deutsch_jozsa_two_bit_balanced_correct :" in module.source


def test_coq_generator_bell_and_ghz3() -> None:
    """Verify Coq generation for the existing Bell and GHZ3 benchmarks."""

    bell_ir = load_raw_ir(EXAMPLES_DIR / "bell_ir.json")
    bell_contract = json.loads((DATA_DIR / "bell.contract.json").read_text(encoding="utf-8"))
    bell_mod = generate_coq_module(bell_ir, bell_contract)
    assert "bell_state_preparation_circuit : Circuit 2 :=" in bell_mod.source
    assert "GateH 0 :: GateCNOT 0 1 :: nil" in bell_mod.source
    assert "Theorem bell_state_preparation_correct :" in bell_mod.source

    ghz_ir = load_raw_ir(EXAMPLES_DIR / "ghz3_ir.json")
    ghz_contract = json.loads((DATA_DIR / "ghz3.contract.json").read_text(encoding="utf-8"))
    ghz_mod = generate_coq_module(ghz_ir, ghz_contract)
    assert "ghz_three_qubit_preparation_circuit : Circuit 3 :=" in ghz_mod.source
    assert "GateH 0 :: GateCNOT 0 1 :: GateCNOT 1 2 :: nil" in ghz_mod.source


def test_dj2_circuit_extractor_equality() -> None:
    """Verify Qiskit circuit -> extractor produces exactly the committed DJ IR."""

    # Constant circuit extraction equality
    const_circuit = build_dj2_constant_circuit()
    const_extracted_ir = circuit_to_ir(const_circuit)
    const_committed_ir = load_raw_ir(EXAMPLES_DIR / "dj2_constant_ir.json")
    assert const_extracted_ir == const_committed_ir

    # Balanced circuit extraction equality
    bal_circuit = build_dj2_balanced_circuit()
    bal_extracted_ir = circuit_to_ir(bal_circuit)
    bal_committed_ir = load_raw_ir(EXAMPLES_DIR / "dj2_balanced_ir.json")
    assert bal_extracted_ir == bal_committed_ir

    # Roundtrip through checked IR and reconstructed Qiskit circuit
    const_checked = check_ir(const_committed_ir)
    assert circuit_to_ir(checked_ir_to_qiskit(const_checked)) == const_committed_ir

    bal_checked = check_ir(bal_committed_ir)
    assert circuit_to_ir(checked_ir_to_qiskit(bal_checked)) == bal_committed_ir


def test_sqir_endianness_asymmetric_states() -> None:
    """Verify SQIR Dirac notation endianness handling for asymmetric quantum states.

    In SQIR/QuantumLib, state kets are ordered from qubit 0 to qubit n-1 (left-to-right):
        v = q_0 ⊗ q_1 ⊗ ... ⊗ q_{n-1} -> ∣b_0, b_1, ..., b_{n-1}⟩.
    In Qiskit little-endian integer index:
        index = sum_{k=0}^{n-1} b_k * 2^k, so b_k = (index >> k) & 1.

    Bell (|00⟩ + |11⟩) and GHZ (|000⟩ + |111⟩) are symmetric under bit reversal,
    so reversing the index produces identical strings:
        00 <-> 00, 11 <-> 11
        000 <-> 000, 111 <-> 111
    Only asymmetric states (like in Deutsch-Jozsa with ancilla on qubit 2) expose
    the difference between little-endian and big-endian Dirac mapping.
    """

    def basis_tokens(active_index: int, n_qubits: int) -> list[str]:
        return ["one" if i == active_index else "zero" for i in range(1 << n_qubits)]

    # 1. Symmetric states (Bell & GHZ): bit-reversal invariant
    # Bell: index 0 is |00⟩, index 3 is |11⟩.
    assert _format_state(basis_tokens(0, 2), num_qubits=2) == "∣0, 0⟩"
    assert _format_state(basis_tokens(3, 2), num_qubits=2) == "∣1, 1⟩"
    # GHZ3: index 0 is |000⟩, index 7 is |111⟩.
    assert _format_state(basis_tokens(0, 3), num_qubits=3) == "∣0, 0, 0⟩"
    assert _format_state(basis_tokens(7, 3), num_qubits=3) == "∣1, 1, 1⟩"

    # 2. Asymmetric states (3 qubits):
    # Case A: Qubit 0 = 1, Qubit 1 = 0, Qubit 2 = 0
    # Qiskit index = 1 * 2^0 = 1.
    # SQIR ket: qubit 0 is position 0, so ∣1, 0, 0⟩.
    # A big-endian mistaken generator would emit ∣0, 0, 1⟩!
    assert _format_state(basis_tokens(1, 3), num_qubits=3) == "∣1, 0, 0⟩"
    assert _format_state(basis_tokens(1, 3), num_qubits=3) != "∣0, 0, 1⟩"

    # Case B: Qubit 0 = 0, Qubit 1 = 0, Qubit 2 = 1
    # Qiskit index = 1 * 2^2 = 4.
    # SQIR ket: qubit 2 is position 2, so ∣0, 0, 1⟩.
    # A big-endian mistaken generator would emit ∣1, 0, 0⟩!
    assert _format_state(basis_tokens(4, 3), num_qubits=3) == "∣0, 0, 1⟩"
    assert _format_state(basis_tokens(4, 3), num_qubits=3) != "∣1, 0, 0⟩"

    # Case C: Qubit 0 = 1, Qubit 1 = 1, Qubit 2 = 0
    # Qiskit index = 1 + 2 = 3.
    # SQIR ket: ∣1, 1, 0⟩. Mistaken big-endian would emit ∣0, 1, 1⟩.
    assert _format_state(basis_tokens(3, 3), num_qubits=3) == "∣1, 1, 0⟩"
    assert _format_state(basis_tokens(3, 3), num_qubits=3) != "∣0, 1, 1⟩"

    # Case D: Qubit 0 = 0, Qubit 1 = 1, Qubit 2 = 1
    # Qiskit index = 2 + 4 = 6.
    # SQIR ket: ∣0, 1, 1⟩. Mistaken big-endian would emit ∣1, 1, 0⟩.
    assert _format_state(basis_tokens(6, 3), num_qubits=3) == "∣0, 1, 1⟩"
    assert _format_state(basis_tokens(6, 3), num_qubits=3) != "∣1, 1, 0⟩"

    # 3. Superposition target states of Deutsch-Jozsa
    # Constant target: 1/√2 |0,0,0⟩ - 1/√2 |0,0,1⟩ (indices 0 and 4)
    # Correct SQIR: ancilla is qubit 2 (3rd ket slot), query qubits 0,1 are 0.
    const_contract = json.loads((DATA_DIR / "dj2_constant.contract.json").read_text(encoding="utf-8"))
    const_target_str = _format_state(const_contract["target_state"], num_qubits=3)
    assert const_target_str == "(/√2)%R .* ∣0, 0, 0⟩ .+ (- /√2)%R .* ∣0, 0, 1⟩"
    assert "∣1, 0, 0⟩" not in const_target_str

    # Balanced target: 1/√2 |1,0,0⟩ - 1/√2 |1,0,1⟩ (indices 1 and 5)
    # Correct SQIR: query qubit 0 is 1, qubit 1 is 0, ancilla qubit 2 is in | - ⟩.
    bal_contract = json.loads((DATA_DIR / "dj2_balanced.contract.json").read_text(encoding="utf-8"))
    bal_target_str = _format_state(bal_contract["target_state"], num_qubits=3)
    assert bal_target_str == "(/√2)%R .* ∣1, 0, 0⟩ .+ (- /√2)%R .* ∣1, 0, 1⟩"
    assert "∣0, 0, 1⟩" not in bal_target_str


def test_lean_generator_dj2_reproducibility(tmp_path: Path) -> None:
    """Verify that Lean generator produces byte-identical code for GeneratedDj2*.lean."""

    lean_dir = PROJECT_ROOT / "lean" / "QuantumValidation"
    for name, module_name in [
        ("dj2_constant", "GeneratedDj2Constant"),
        ("dj2_balanced", "GeneratedDj2Balanced"),
    ]:
        ir_data = load_raw_ir(EXAMPLES_DIR / f"{name}_ir.json")
        contract_data = json.loads((DATA_DIR / f"{name}.contract.json").read_text(encoding="utf-8"))
        generated = generate_lean_module(ir_data, contract_data)
        committed = lean_dir / f"{module_name}.lean"
        assert generated.source == committed.read_text(encoding="utf-8")

        # Windows LF canonical byte check
        out_file = tmp_path / f"{module_name}.lean"
        write_lean_module(ir_data, contract_data, out_file)
        assert out_file.read_bytes() == generated.source.encode("utf-8")
