"""Ask Lean to check the proof generated from a live Qiskit rewrite."""

from __future__ import annotations

import shutil
import subprocess

from qiskit import QuantumCircuit

from fqv.backend.lean.transpilation import generate_transpilation_lean_module
from fqv.pipeline.transpilation import TranspilationConfig, transpile_check_and_certify


def test_duplicate_h_certificate_compiles(tmp_path) -> None:
    """Cover Qiskit, checked IR, certificate replay, generation, and Lean."""

    lake = shutil.which("lake")
    assert lake is not None, "Install Lean and run lake build before integration tests"

    circuit = QuantumCircuit(1, name="duplicate_h")
    circuit.h(0)
    circuit.h(0)
    _, report, certificate = transpile_check_and_certify(
        circuit,
        config=TranspilationConfig(optimization_level=1),
    )
    assert report.passed

    generated = generate_transpilation_lean_module(certificate)
    destination = tmp_path / "DuplicateHTranspilation.lean"
    destination.write_text(generated.source, encoding="utf-8", newline="\n")
    # Compilation is the evidence; source-string assertions alone cannot show
    # that the emitted theorem is meaningful or accepted by Lean's kernel.
    result = subprocess.run(
        [lake, "env", "lean", str(destination)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
