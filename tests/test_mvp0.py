from __future__ import annotations

import numpy as np
from qiskit.quantum_info import Statevector

from fqv.frontend.qiskit.circuits import (
    bell_contract,
    build_bell_circuit,
    build_bell_minus_circuit,
)
from fqv.frontend.qiskit.extraction import circuit_to_ir
from fqv.frontend.qiskit.verification import verify_contract


def test_bell_contract_passes() -> None:
    report = verify_contract(
        build_bell_circuit(),
        bell_contract(),
        shots=4096,
        seed=7,
    )

    assert report.passed, report.render_text()


def test_same_statistics_do_not_imply_same_state() -> None:
    plus_state = Statevector.from_instruction(
        build_bell_circuit()
    )

    minus_state = Statevector.from_instruction(
        build_bell_minus_circuit()
    )

    plus_probabilities = plus_state.probabilities()
    minus_probabilities = minus_state.probabilities()

    assert np.allclose(
        plus_probabilities,
        minus_probabilities,
    )

    assert not plus_state.equiv(minus_state)


def test_phase_counterexample_fails_contract() -> None:
    report = verify_contract(
        build_bell_minus_circuit(),
        bell_contract(),
        shots=4096,
        seed=7,
    )

    target_state_check = next(
        check
        for check in report.checks
        if check.name == "target-state"
    )

    assert not target_state_check.passed
    assert not report.passed


def test_bell_ir() -> None:
    ir = circuit_to_ir(
        build_bell_circuit()
    )

    assert ir == {
        "schema_version": "0.1",
        "name": "bell_phi_plus",
        "qubits": 2,
        "operations": [
            {
                "gate": "H",
                "targets": [0],
            },
            {
                "gate": "CNOT",
                "controls": [0],
                "targets": [1],
            },
        ],
    }
