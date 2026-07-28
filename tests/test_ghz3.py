from __future__ import annotations

import numpy as np
import pytest
from qiskit.quantum_info import Statevector

from fqv.frontend.qiskit.circuits import (
    build_ghz_circuit,
    build_ghz3_circuit,
    ghz3_contract,
)
from fqv.frontend.qiskit.extraction import circuit_to_ir
from fqv.frontend.qiskit.verification import verify_contract
from fqv.pipeline.transpilation import (
    TranspilationConfig,
    transpile_and_check,
)


def test_ghz3_contract_passes() -> None:
    report = verify_contract(
        build_ghz3_circuit(),
        ghz3_contract(),
        shots=4096,
        seed=7,
    )

    assert report.passed, report.render_text()


def test_ghz3_relative_phase_mutation_fails() -> None:
    mutated = build_ghz3_circuit()
    mutated.z(0)
    report = verify_contract(
        mutated,
        ghz3_contract(),
        shots=4096,
        seed=7,
    )

    assert not report.passed
    target_check = next(
        check
        for check in report.checks
        if check.name == "target-state"
    )
    assert not target_check.passed


def test_ghz3_ir_matches_general_gate_positions() -> None:
    ir = circuit_to_ir(build_ghz3_circuit())

    assert ir["qubits"] == 3
    assert ir["operations"][2] == {
        "gate": "CNOT",
        "controls": [1],
        "targets": [2],
    }


def test_ghz3_transpilation_preserves_operator() -> None:
    _, report = transpile_and_check(
        build_ghz3_circuit(),
        config=TranspilationConfig(
            optimization_level=2,
            seed_transpiler=11,
        ),
    )

    assert report.passed, report.render_text()


@pytest.mark.parametrize("num_qubits", [1, 2, 3, 4, 5])
def test_parametric_ghz_family(num_qubits: int) -> None:
    circuit = build_ghz_circuit(num_qubits)
    state = Statevector.from_instruction(circuit)
    expected = np.zeros(2 ** num_qubits, dtype=complex)
    expected[0] = 1.0 / np.sqrt(2.0)
    expected[-1] = 1.0 / np.sqrt(2.0)

    assert np.allclose(state.data, expected)


def test_parametric_ghz_rejects_empty_register() -> None:
    with pytest.raises(ValueError, match="at least one qubit"):
        build_ghz_circuit(0)
