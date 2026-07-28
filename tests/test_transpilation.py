from __future__ import annotations

from qiskit import QuantumCircuit

from fqv.frontend.qiskit.circuits import build_bell_circuit
from fqv.pipeline.transpilation import (
    TranspilationConfig,
    check_operator_equivalence,
    transpile_and_check,
)


def test_bell_transpilation_preserves_operator() -> None:
    transpiled, report = transpile_and_check(
        build_bell_circuit(),
        config=TranspilationConfig(
            optimization_level=2,
            seed_transpiler=11,
        ),
    )

    assert transpiled.num_qubits == 2
    assert report.passed, report.render_text()
    assert report.equivalent_up_to_global_phase


def test_transpilation_is_reproducible() -> None:
    circuit = build_bell_circuit()
    config = TranspilationConfig(
        optimization_level=2,
        seed_transpiler=11,
    )

    first, first_report = transpile_and_check(
        circuit,
        config=config,
    )
    second, second_report = transpile_and_check(
        circuit,
        config=config,
    )

    assert first == second
    assert first_report.to_dict() == second_report.to_dict()


def test_non_equivalent_circuit_is_rejected() -> None:
    source = build_bell_circuit()
    mutated = source.copy()
    mutated.x(1)
    config = TranspilationConfig()

    report = check_operator_equivalence(
        source,
        mutated,
        config=config,
    )

    assert not report.passed
    assert not report.equivalent_up_to_global_phase


def test_complete_operator_is_stronger_than_one_input() -> None:
    source = QuantumCircuit(1)
    candidate = QuantumCircuit(1)
    candidate.z(0)

    # Both circuits preserve |0>, but they differ on superpositions.
    report = check_operator_equivalence(
        source,
        candidate,
        config=TranspilationConfig(),
    )

    assert not report.passed
