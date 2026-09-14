"""Generate Lean obligations from validated exact-rewrite certificates."""

from __future__ import annotations

from pathlib import Path

from fqv.backend.lean.generator import GeneratedLeanModule, _format_gate, _lean_identifier
from fqv.domain.transpilation import (
    TranspilationCertificate,
    certify_self_inverse_cancellations,
)


def _format_circuit(certificate: TranspilationCertificate, *, source: bool) -> str:
    """Serialize one certificate endpoint with the established Lean syntax."""

    circuit = certificate.source if source else certificate.candidate
    return ", ".join(_format_gate(operation) for operation in circuit.operations)


def _rewrite_lemmas(certificate: TranspilationCertificate) -> str:
    """Include exactly the lemmas used, keeping generated Lean warning-free."""

    names = {
        "X": "x_involutive",
        "Z": "z_involutive",
        "H": "h_apply_twice",
        "CNOT": "cnot_involutive",
        "SWAP": "swap_involutive",
    }
    return ",\n    ".join(
        dict.fromkeys(names[step.gate.value] for step in certificate.steps)
    )


def generate_transpilation_lean_module(
    certificate: TranspilationCertificate,
) -> GeneratedLeanModule:
    """Emit an all-input equivalence theorem after replaying the certificate."""

    replayed = certify_self_inverse_cancellations(
        certificate.source, certificate.candidate
    )
    if replayed.steps != certificate.steps:
        raise ValueError("certificate steps do not match deterministic replay")

    prefix = _lean_identifier(f"{certificate.source.name} transpilation")
    source_name = f"generated{prefix}Source"
    candidate_name = f"generated{prefix}Candidate"
    theorem_name = f"generated{prefix}Correct"
    source_gates = _format_circuit(certificate, source=True)
    candidate_gates = _format_circuit(certificate, source=False)
    steps = ", ".join(
        f"{step.rule}:{step.gate.value}@{step.position}"
        for step in certificate.steps
    )
    rewrite_lemmas = _rewrite_lemmas(certificate)

    source = f"""import QuantumValidation.Transpilation

/-!
Generated exact transpilation certificate.

Recognized steps: {steps}
Regenerate this module instead of editing it by hand.
-/

namespace QuantumValidation
namespace General

def {source_name} : Circuit {certificate.source.num_qubits} :=
  [{source_gates}]

def {candidate_name} : Circuit {certificate.candidate.num_qubits} :=
  [{candidate_gates}]

/-- The generated endpoints agree on every possible input state. -/
theorem {theorem_name} :
    CircuitEquivalent {source_name} {candidate_name} := by
  intro input
  simp [
    {source_name},
    {candidate_name},
    denote,
    {rewrite_lemmas}
  ]

end General
end QuantumValidation
"""
    return GeneratedLeanModule(source=source, theorem_name=theorem_name)


def write_transpilation_lean_module(
    certificate: TranspilationCertificate,
    destination: str | Path,
) -> Path:
    """Write the Lean obligation; a later Lean invocation checks it."""

    output = Path(destination)
    module = generate_transpilation_lean_module(certificate)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(module.source, encoding="utf-8", newline="\n")
    return output
