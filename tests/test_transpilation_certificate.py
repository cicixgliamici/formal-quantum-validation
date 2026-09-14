"""Exercise the Qiskit-to-certificate-to-formal-backend vertical slice."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest
from qiskit import QuantumCircuit

from fqv.backend.coq.transpilation import generate_transpilation_coq_module
from fqv.backend.lean.transpilation import generate_transpilation_lean_module
from fqv.domain.transpilation import TranspilationStep, UnsupportedTranspilationError
from fqv.ir.checked import GateName
from fqv.ir.validation import check_ir
from fqv.pipeline.transpilation import TranspilationConfig, transpile_check_and_certify
from fqv.pipeline.transpilation_certificate import (
    certify_self_inverse_cancellations,
    write_transpilation_certificate,
)


def _duplicate_h_circuit() -> QuantumCircuit:
    """Keep the source small while exercising extraction and Qiskit optimization."""

    circuit = QuantumCircuit(1, name="duplicate_h")
    circuit.h(0)
    circuit.h(0)
    return circuit


def test_qiskit_duplicate_h_produces_formal_obligations() -> None:
    transpiled, report, certificate = transpile_check_and_certify(
        _duplicate_h_circuit(),
        config=TranspilationConfig(optimization_level=1),
    )

    assert report.passed
    assert not transpiled.data
    assert certificate.steps == (
        TranspilationStep("cancel_self_inverse", 0, GateName.H, (0,)),
    )

    lean = generate_transpilation_lean_module(certificate)
    coq = generate_transpilation_coq_module(certificate)
    assert "CircuitEquivalent" in lean.source
    assert "h_apply_twice" in lean.source
    assert "run duplicate_h_transpilation_source" in coq.source
    assert "solve_circuit" in coq.source


def test_formal_generators_reject_a_mutated_trace() -> None:
    _, _, certificate = transpile_check_and_certify(
        _duplicate_h_circuit(),
        config=TranspilationConfig(optimization_level=1),
    )
    mutated = replace(
        certificate,
        steps=(
            TranspilationStep("cancel_self_inverse", 1, GateName.H, (0,)),
        ),
    )

    with pytest.raises(ValueError, match="deterministic replay"):
        generate_transpilation_lean_module(mutated)
    with pytest.raises(ValueError, match="deterministic replay"):
        generate_transpilation_coq_module(mutated)


def test_certificate_serialization_is_deterministic(tmp_path) -> None:
    """Keep both checked endpoints and the replayable step in one artifact."""

    _, _, certificate = transpile_check_and_certify(
        _duplicate_h_circuit(),
        config=TranspilationConfig(optimization_level=1),
    )
    first = write_transpilation_certificate(certificate, tmp_path / "first.json")
    second = write_transpilation_certificate(certificate, tmp_path / "second.json")

    assert first.read_bytes() == second.read_bytes()
    payload = json.loads(first.read_text(encoding="utf-8"))
    assert payload["source"]["operations"] == [
        {"gate": "H", "targets": [0]},
        {"gate": "H", "targets": [0]},
    ]
    assert payload["candidate"]["operations"] == []
    assert payload["steps"] == [
        {
            "controls": [],
            "gate": "H",
            "position": 0,
            "rule": "cancel_self_inverse",
            "targets": [0],
        }
    ]
    assert payload["schema_version"] == "0.2"


def test_unchanged_circuit_is_outside_the_certificate_catalog() -> None:
    """Fail closed when Qiskit has not performed the supported rewrite."""

    with pytest.raises(UnsupportedTranspilationError, match="solely by certified"):
        transpile_check_and_certify(
            _duplicate_h_circuit(),
            config=TranspilationConfig(optimization_level=0),
        )


@pytest.mark.parametrize(
    ("gate", "operation", "expected_targets", "expected_controls"),
    [
        (GateName.X, {"gate": "X", "targets": [0]}, (0,), ()),
        (GateName.Z, {"gate": "Z", "targets": [0]}, (0,), ()),
        (GateName.H, {"gate": "H", "targets": [0]}, (0,), ()),
        (GateName.CNOT, {"gate": "CNOT", "controls": [0], "targets": [1]}, (1,), (0,)),
        (GateName.SWAP, {"gate": "SWAP", "targets": [0, 1]}, (0, 1), ()),
    ],
)
def test_every_self_inverse_gate_can_be_certified(
    gate: GateName,
    operation: dict[str, object],
    expected_targets: tuple[int, ...],
    expected_controls: tuple[int, ...],
) -> None:
    """Exercise the full rule catalog independently of Qiskit pass choices."""

    source = check_ir(
        {
            "schema_version": "0.1",
            "name": f"duplicate_{gate.value.lower()}",
            "qubits": 2,
            "operations": [operation, operation],
        }
    )
    candidate = check_ir(
        {
            "schema_version": "0.1",
            "name": "empty_candidate",
            "qubits": 2,
            "operations": [],
        }
    )

    certificate = certify_self_inverse_cancellations(source, candidate)

    assert certificate.steps == (
        TranspilationStep(
            "cancel_self_inverse",
            0,
            gate,
            expected_targets,
            expected_controls,
        ),
    )
    assert "CircuitEquivalent" in generate_transpilation_lean_module(certificate).source
    assert "solve_circuit" in generate_transpilation_coq_module(certificate).source
