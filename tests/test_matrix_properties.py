"""Unit tests for the matrices produced by the checked-IR adapter.

Literal matrices are independent expected values, not copies obtained from
Qiskit. Rows are output basis indices and columns are input basis indices.
The two-qubit fixtures follow the project's little-endian convention.
"""

from __future__ import annotations

import numpy as np
import pytest
from qiskit.quantum_info import Operator

from fqv.frontend.qiskit.conversion import checked_ir_to_qiskit
from fqv.ir.validation import check_ir

GATE_CASES = [
    pytest.param({"gate": "I", "targets": [0]}, np.eye(2), id="identity"),
    pytest.param({"gate": "X", "targets": [0]}, [[0, 1], [1, 0]], id="pauli-x"),
    pytest.param({"gate": "Z", "targets": [0]}, [[1, 0], [0, -1]], id="pauli-z"),
    pytest.param({"gate": "H", "targets": [0]},
                 np.array([[1, 1], [1, -1]]) / np.sqrt(2), id="hadamard"),
    pytest.param({"gate": "CNOT", "controls": [0], "targets": [1]},
                 [[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]],
                 id="cnot-control-zero"),
    pytest.param({"gate": "SWAP", "targets": [0, 1]},
                 [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]],
                 id="swap"),
]

# Tracelessness is a Pauli-specific claim, so unrelated gates must not create
# vacuous passing parameter cases for this test.
PAULI_CASES = [case for case in GATE_CASES if case.values[0]["gate"] in {"X", "Z"}]


def _gate_matrix(operation: dict, dimension: int) -> np.ndarray:
    """Exercise validation and conversion before observing Qiskit's operator."""
    raw = {"schema_version": "0.1", "name": "matrix_unit_test",
           "qubits": dimension.bit_length() - 1, "operations": [operation]}
    return Operator(checked_ir_to_qiskit(check_ir(raw))).data


class TestSupportedGateMatrices:
    """Check entries and algebraic invariants for every IR gate.

    Each method reaches the real IR-to-Qiskit adapter. An entry-ordering error
    can preserve unitarity, so matching the literal matrix is a separate check.
    Absolute tolerance covers floating-point roundoff, not physical noise.
    """

    @pytest.mark.parametrize("operation,expected", GATE_CASES)
    def test_entries_match_the_declared_gate(self, operation: dict, expected) -> None:
        actual = _gate_matrix(operation, len(expected))
        np.testing.assert_allclose(actual, expected, atol=1e-12, rtol=0)

    @pytest.mark.parametrize("operation,expected", GATE_CASES)
    def test_adjoint_is_a_two_sided_inverse(self, operation: dict, expected) -> None:
        matrix = _gate_matrix(operation, len(expected))
        identity = np.eye(len(expected))
        # Both products matter when teaching the matrix definition of unitarity.
        np.testing.assert_allclose(matrix.conj().T @ matrix, identity, atol=1e-12, rtol=0)
        np.testing.assert_allclose(matrix @ matrix.conj().T, identity, atol=1e-12, rtol=0)

    @pytest.mark.parametrize("operation,expected", GATE_CASES)
    def test_supported_gates_are_self_inverse(self, operation: dict, expected) -> None:
        matrix = _gate_matrix(operation, len(expected))
        # This property holds for IR 0.1's six gates, not for every unitary gate.
        np.testing.assert_allclose(matrix @ matrix, np.eye(len(expected)), atol=1e-12, rtol=0)

    @pytest.mark.parametrize("operation,expected", GATE_CASES)
    def test_complex_inner_products_and_norms_are_preserved(self, operation: dict, expected) -> None:
        matrix = _gate_matrix(operation, len(expected))
        indices = np.arange(1, len(expected) + 1)
        left = indices + 1j * indices[::-1]
        right = indices[::-1] - 2j * indices
        left /= np.linalg.norm(left)
        right /= np.linalg.norm(right)
        # Complex inputs exercise conjugation; real-only inputs could miss it.
        assert np.vdot(matrix @ left, matrix @ right) == pytest.approx(np.vdot(left, right), abs=1e-12)
        assert np.linalg.norm(matrix @ left) == pytest.approx(1.0, abs=1e-12)

    @pytest.mark.parametrize("operation,expected", GATE_CASES)
    def test_inverses_match_adjoint(self, operation: dict, expected) -> None:
        matrix = _gate_matrix(operation, len(expected))
        np.testing.assert_allclose(np.linalg.inv(matrix), matrix.conj().T, atol=1e-12, rtol=0)


class TestMatrixCounterexamples:
    """Show why weaker matrix checks must not be mistaken for unitarity.

    These are mathematical negative controls. Arbitrary matrices are not an IR
    input format; the tests do not claim that the project supports importing them.
    """

    @pytest.mark.parametrize("matrix", [
        np.zeros((2, 2)), np.diag([1, 0]), 2 * np.eye(2),
        np.array([[1, 1], [1, -1]]), np.array([[1, 1], [0, 0]]),
    ], ids=["zero", "projector", "scaled-identity", "unnormalized-h", "duplicate-columns"])
    def test_nonunitary_matrices_fail_the_adjoint_identity(self, matrix: np.ndarray) -> None:
        assert not np.allclose(matrix.conj().T @ matrix, np.eye(2), atol=1e-12, rtol=0)
        assert not Operator(matrix).is_unitary(atol=1e-12, rtol=0)

    def test_normalized_columns_can_still_destroy_a_superposition(self) -> None:
        matrix = np.array([[1, 1], [0, 0]], dtype=complex)
        np.testing.assert_allclose(np.linalg.norm(matrix, axis=0), [1, 1])
        minus_state = np.array([1, -1]) / np.sqrt(2)
        # Both basis vectors have normalized images, but the columns coincide.
        np.testing.assert_allclose(matrix @ minus_state, [0, 0], atol=1e-12)

    def test_complex_unitarity_requires_conjugate_transpose(self) -> None:
        matrix = np.diag([1, 1j])
        np.testing.assert_allclose(matrix.conj().T @ matrix, np.eye(2))
        assert not np.allclose(matrix.T @ matrix, np.eye(2))
        # This diagnostic example is unitary but neither Hermitian nor involutive.
        assert not np.allclose(matrix, matrix.conj().T)
        assert not np.allclose(matrix @ matrix, np.eye(2))


class TestAdvancedMatrixInvariants:
    """Evaluate spectral properties not covered by direct gate action."""

    @pytest.mark.parametrize("operation,expected", GATE_CASES)
    def test_matrix_determinants_are_phases(self, operation: dict, expected) -> None:
        matrix = _gate_matrix(operation, len(expected))
        det = np.linalg.det(matrix)
        assert np.abs(det) == pytest.approx(1.0, abs=1e-12)

    @pytest.mark.parametrize("operation,expected", GATE_CASES)
    def test_matrix_eigenvalues_lie_on_unit_circle(self, operation: dict, expected) -> None:
        matrix = _gate_matrix(operation, len(expected))
        eigenvalues = np.linalg.eigvals(matrix)
        np.testing.assert_allclose(np.abs(eigenvalues), 1.0, atol=1e-12, rtol=0)

    @pytest.mark.parametrize("operation,expected", PAULI_CASES)
    def test_pauli_matrices_are_traceless(self, operation: dict, expected) -> None:
        matrix = _gate_matrix(operation, len(expected))
        trace = np.trace(matrix)
        assert np.abs(trace) == pytest.approx(0.0, abs=1e-12)
