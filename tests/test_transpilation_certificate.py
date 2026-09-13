"""Exercise the Qiskit-to-certificate-to-formal-backend vertical slice."""

from __future__ import annotations

import json
from dataclasses import replace

import pytest
from qiskit import QuantumCircuit

from fqv.backend.coq.transpilation import generate_transpilation_coq_module
from fqv.backend.lean.transpilation import generate_transpilation_lean_module
from fqv.domain.transpilation import TranspilationStep, UnsupportedTranspilationError
from fqv.pipeline.transpilation import TranspilationConfig, transpile_check_and_certify
from fqv.pipeline.transpilation_certificate import write_transpilation_certificate


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
    assert certificate.steps == (TranspilationStep("cancel_h_h", 0, 0),)

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
        steps=(TranspilationStep("cancel_h_h", 1, 0),),
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
        {"position": 0, "rule": "cancel_h_h", "target": 0}
    ]


def test_unchanged_circuit_is_outside_the_certificate_catalog() -> None:
    """Fail closed when Qiskit has not performed the supported rewrite."""

    with pytest.raises(UnsupportedTranspilationError, match="solely by certified"):
        transpile_check_and_certify(
            _duplicate_h_circuit(),
            config=TranspilationConfig(optimization_level=0),
        )
