"""Compile the certificate generated from a live Qiskit optimization."""

from qiskit import QuantumCircuit

from fqv.backend.coq.transpilation import generate_transpilation_coq_module
from fqv.pipeline.transpilation import TranspilationConfig, transpile_check_and_certify


def test_duplicate_h_certificate_compiles(tmp_path, coq_compile) -> None:
    """Connect Qiskit optimization to an exact SQIR operator theorem."""

    circuit = QuantumCircuit(1, name="duplicate_h")
    circuit.h(0)
    circuit.h(0)
    _, report, certificate = transpile_check_and_certify(
        circuit,
        config=TranspilationConfig(optimization_level=1),
    )
    assert report.passed

    generated = generate_transpilation_coq_module(certificate)
    result = coq_compile(generated.source, tmp_path / "DuplicateHTranspilation.v")
    assert result.returncode == 0, result.stdout + result.stderr
