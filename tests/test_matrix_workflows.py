"""Functional tests connecting matrix identities to actual application verdicts."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, Statevector

from fqv.cli import main
from fqv.frontend.qiskit.circuits import bell_contract, build_bell_circuit
from fqv.frontend.qiskit.conversion import checked_ir_to_qiskit
from fqv.frontend.qiskit.extraction import circuit_to_ir
from fqv.frontend.qiskit.verification import verify_contract
from fqv.ir.validation import check_ir
from fqv.pipeline.transpilation import TranspilationConfig, transpile_and_check
from fqv.pipeline.verify import verify


def _mutated_bell_ir(mutation: str) -> dict:
    """Change semantics using supported gates, keeping every circuit unitary."""
    raw = circuit_to_ir(build_bell_circuit())
    if mutation == "reverse-order":
        raw["operations"].reverse()
    elif mutation == "reverse-control":
        raw["operations"][1] = {"gate": "CNOT", "controls": [1], "targets": [0]}
    elif mutation == "relative-phase":
        raw["operations"].append({"gate": "Z", "targets": [0]})
    return raw


class TestBellMatrixWorkflow:
    """Follow IR -> operator -> contract report, then check transpilation.

    An independent matrix product specifies execution order: H acts first,
    so its matrix is on the right of CNOT. Qubit zero is the right Kronecker
    factor. These checks distinguish a correct unitary from the intended one.
    """

    def test_bell_matrix_and_contract_agree(self) -> None:
        circuit = checked_ir_to_qiskit(check_ir(circuit_to_ir(build_bell_circuit())))
        hadamard = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
        cnot = np.array([[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]])
        expected = cnot @ np.kron(np.eye(2), hadamard)
        np.testing.assert_allclose(Operator(circuit).data, expected, atol=1e-12, rtol=0)
        np.testing.assert_allclose(expected @ [1, 0, 0, 0], bell_contract().target_state)
        report = verify(circuit, bell_contract(), verifier=verify_contract)
        assert report.passed, report.render_text()

    @pytest.mark.parametrize("level", [0, 1, 2, 3])
    def test_transpilation_preserves_unitarity_and_the_full_operator(self, level: int) -> None:
        source = build_bell_circuit()
        candidate, report = transpile_and_check(source, config=TranspilationConfig(optimization_level=level))
        matrix = Operator(candidate).data
        np.testing.assert_allclose(matrix.conj().T @ matrix, np.eye(4), atol=1e-12, rtol=0)
        assert report.passed, report.render_text()
        assert report.max_phase_aligned_error <= 1e-12


class TestMatrixContractCli:
    """Exercise actual files, CLI exit codes, and serialized scientific evidence.

    Every tested circuit remains unitary. Only the reference prepares the
    declared Bell state; mutations demonstrate that unitarity is insufficient.
    The tests call the entry-point function with real argv and temporary files.
    """

    @pytest.mark.parametrize("mutation,expected_exit", [
        ("none", 0), ("reverse-order", 1), ("reverse-control", 1), ("relative-phase", 1),
    ])
    def test_unitarity_does_not_replace_the_state_contract(
        self, mutation: str, expected_exit: int, tmp_path: Path, monkeypatch,
    ) -> None:
        raw = _mutated_bell_ir(mutation)
        circuit = checked_ir_to_qiskit(check_ir(raw))
        assert Operator(circuit).is_unitary()
        ir_path, report_path = tmp_path / "circuit.json", tmp_path / "report.json"
        ir_path.write_text(json.dumps(raw), encoding="utf-8")
        monkeypatch.setattr("sys.argv", ["fqv-verify", "--ir", str(ir_path),
                                        "--json-report", str(report_path)])
        assert main() == expected_exit
        report = json.loads(report_path.read_text(encoding="utf-8"))
        state_check = next(check for check in report["checks"] if check["name"] == "target-state")
        assert state_check["passed"] is (expected_exit == 0)
        assert report["passed"] is (expected_exit == 0)


class TestDisjointGateWorkflows:
    """Ensure operations on disjoint qubits and global phases work correctly."""

    def test_disjoint_gates_commute_in_execution(self) -> None:
        """H on q0 then X on q1 is the same global matrix as X on q1 then H on q0."""
        circuit1 = QuantumCircuit(2)
        circuit1.h(0)
        circuit1.x(1)
        
        circuit2 = QuantumCircuit(2)
        circuit2.x(1)
        circuit2.h(0)
        
        matrix1 = Operator(circuit1).data
        matrix2 = Operator(circuit2).data
        
        np.testing.assert_allclose(matrix1, matrix2, atol=1e-12, rtol=0)

    def test_global_phase_does_not_affect_measurement_probabilities(self) -> None:
        """A global phase changes the matrix but not the observable probabilities."""
        circuit = build_bell_circuit()
        matrix1 = Operator(circuit).data
        
        circuit_with_phase = circuit.copy()
        circuit_with_phase.global_phase = np.pi / 4
        matrix2 = Operator(circuit_with_phase).data
        
        # The matrices differ by a scalar factor
        assert not np.allclose(matrix1, matrix2, atol=1e-12, rtol=0)
        
        # The probabilities are identical
        probs1 = Statevector(circuit).probabilities()
        probs2 = Statevector(circuit_with_phase).probabilities()
        
        np.testing.assert_allclose(probs1, probs2, atol=1e-12, rtol=0)
