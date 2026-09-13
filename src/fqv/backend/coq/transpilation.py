"""Generate Coq/SQIR obligations from exact-rewrite certificates."""

from __future__ import annotations

from pathlib import Path

from fqv.backend.coq.generator import GeneratedCoqModule, _coq_identifier, _format_gate
from fqv.domain.transpilation import TranspilationCertificate, certify_h_cancellations


def _format_circuit(certificate: TranspilationCertificate, *, source: bool) -> str:
    """Use constructor lists so SQIR composition notation cannot interfere."""

    circuit = certificate.source if source else certificate.candidate
    return " :: ".join([*(_format_gate(op) for op in circuit.operations), "nil"])


def generate_transpilation_coq_module(
    certificate: TranspilationCertificate,
) -> GeneratedCoqModule:
    """Emit a concrete complete-operator equality checked through SQIR."""

    replayed = certify_h_cancellations(certificate.source, certificate.candidate)
    if replayed.steps != certificate.steps:
        raise ValueError("certificate steps do not match deterministic replay")

    prefix = _coq_identifier(f"{certificate.source.name} transpilation")
    source_name = f"{prefix}_source"
    candidate_name = f"{prefix}_candidate"
    theorem_name = f"{prefix}_correct"
    source_gates = _format_circuit(certificate, source=True)
    candidate_gates = _format_circuit(certificate, source=False)

    source = f"""From QuantumValidation Require Import Circuit.
Import QuantumValidationSQIR.

(* Generated exact transpilation certificate. Regenerate instead of editing. *)
Definition {source_name} : Circuit {certificate.source.num_qubits} :=
  {source_gates}.

Definition {candidate_name} : Circuit {certificate.candidate.num_qubits} :=
  {candidate_gates}.

(* Both circuits denote exactly the same complete SQIR operator. *)
Theorem {theorem_name} :
  run {source_name} = run {candidate_name}.
Proof.
  unfold {source_name}, {candidate_name}.
  solve_circuit.
Qed.
"""
    return GeneratedCoqModule(source=source, theorem_name=theorem_name)


def write_transpilation_coq_module(
    certificate: TranspilationCertificate,
    destination: str | Path,
) -> Path:
    """Write the Coq obligation; a later coqc invocation checks it."""

    output = Path(destination)
    module = generate_transpilation_coq_module(certificate)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(module.source, encoding="utf-8", newline="\n")
    return output
