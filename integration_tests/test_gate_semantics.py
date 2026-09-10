"""Compare Qiskit gate execution with kernel-checked Lean obligations.

Run after ``lake build`` with ``python -m pytest integration_tests``. These
tests invoke Lean rather than merely inspecting generated source strings.
They live outside the fast ``tests`` directory because both toolchains are
required; CI runs them in the Lean job after installing Python dependencies.

For registers of one, two, and three qubits, every supported gate placement
is exercised on every computational-basis input. Qiskit supplies the expected
amplitudes, the production extractor and generator translate the case, and
Lean checks equality against QuantumValidation.General.Gate.apply. This is a finite
cross-system regression, not a proof of the Python or Qiskit implementations.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Iterator
from itertools import permutations
from pathlib import Path

import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from fqv.backend.lean.generator import generate_lean_module
from fqv.domain.amplitudes import AmplitudeToken, decode_amplitude
from fqv.frontend.qiskit.extraction import circuit_to_ir

PROJECT_ROOT = Path(__file__).parents[1]
LEAN_IMPORT = "import QuantumValidation.GeneralCircuit\n"


def _gate_circuits(num_qubits: int) -> Iterator[QuantumCircuit]:
    """Use Qiskit's own gate constructors, independently of the IR converter."""
    for gate in ("id", "x", "z", "h"):
        for target in range(num_qubits):
            circuit = QuantumCircuit(num_qubits, name=f"{gate}_{target}")
            getattr(circuit, gate)(target)
            yield circuit
    for gate in ("cx", "swap"):
        # Both operand orders are deliberate, including the symmetric SWAP.
        # Three-qubit cases also cover non-adjacent operands and spectator bits.
        for first, second in permutations(range(num_qubits), 2):
            circuit = QuantumCircuit(num_qubits, name=f"{gate}_{first}_{second}")
            getattr(circuit, gate)(first, second)
            yield circuit


def _amplitude_token(value: complex) -> str:
    """Recognize only constants representable exactly by the contract format."""
    matches = [token.value for token in AmplitudeToken
               if abs(value - decode_amplitude(token)) <= 1e-12]
    # Never round arbitrary amplitudes into a theorem about a different state.
    # The selected gates on basis inputs only produce this finite vocabulary.
    assert len(matches) == 1, f"Unsupported or ambiguous Qiskit amplitude: {value}"
    return matches[0]


def _case_contract(circuit: QuantumCircuit, basis_index: int) -> dict:
    """Observe Qiskit first, then encode its output as the Lean proof target."""
    amplitudes = [0] * (2 ** circuit.num_qubits)
    amplitudes[basis_index] = 1
    output = Statevector(amplitudes).evolve(circuit)
    return {
        "schema_version": "0.1",
        "name": f"Gate {circuit.name} Input {basis_index}",
        "qubits": circuit.num_qubits,
        "initial_state": [_amplitude_token(value) for value in amplitudes],
        "target_state": [_amplitude_token(value) for value in output.data],
        "fidelity_threshold": 1.0 - 1e-12,
        "resources": {
            "gate_counts": dict(circuit.count_ops()), "allow_extra_gates": False,
        },
        "probabilities": [],
    }


def _obligation(circuit: QuantumCircuit, contract: dict) -> str:
    """Keep production translation in the path, including operand extraction."""
    source = generate_lean_module(circuit_to_ir(circuit), contract).source
    assert source.startswith(LEAN_IMPORT)
    # Imports must precede declarations when combining many generated modules.
    return source.removeprefix(LEAN_IMPORT)


def _run_lean(source: str, destination: Path) -> subprocess.CompletedProcess[str]:
    """Compile real theorem bodies; missing Lean is an integration failure."""
    lake = shutil.which("lake")
    assert lake is not None, "Install Lean and run lake build before integration tests"
    destination.write_text(source, encoding="utf-8", newline="\n")
    return subprocess.run(
        [lake, "env", "lean", str(destination)],
        cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=600, check=False,
    )


@pytest.mark.parametrize("num_qubits,expected_cases", [(1, 8), (2, 48), (3, 192)])
def test_all_gate_basis_cases_compile(
    num_qubits: int, expected_cases: int, tmp_path: Path,
) -> None:
    obligations = [
        _obligation(circuit, _case_contract(circuit, basis_index))
        for circuit in _gate_circuits(num_qubits)
        for basis_index in range(2 ** num_qubits)
    ]
    assert len(obligations) == expected_cases
    result = _run_lean(LEAN_IMPORT + "\n".join(obligations), tmp_path / "Gates.lean")
    assert result.returncode == 0, result.stdout + result.stderr


def test_lean_rejects_a_mutated_qiskit_target(tmp_path: Path) -> None:
    circuit = QuantumCircuit(1, name="h_mutation")
    circuit.h(0)
    contract = _case_contract(circuit, 0)
    # Flip one branch's sign while preserving normalization. If the harness
    # merely generated text or ignored the target, this false theorem would pass.
    contract["target_state"][1] = "minus_inv_sqrt_two"
    result = _run_lean(
        LEAN_IMPORT + _obligation(circuit, contract), tmp_path / "Mutation.lean",
    )
    assert result.returncode != 0
    assert "unsolved goals" in result.stdout, result.stdout + result.stderr
