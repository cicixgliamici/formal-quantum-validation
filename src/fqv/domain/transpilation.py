"""Backend-neutral certificates for exact circuit rewrites."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fqv.ir.checked import CheckedCircuitIr, CheckedOperation, GateName
from fqv.ir.serialization import checked_ir_to_dict


@dataclass(frozen=True)
class TranspilationStep:
    """One local rewrite, positioned in the circuit produced by prior steps."""

    rule: str
    position: int
    gate: GateName
    targets: tuple[int, ...]
    controls: tuple[int, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return the stable JSON representation shared by formal backends."""

        return {
            "rule": self.rule,
            "position": self.position,
            "gate": self.gate.value,
            "targets": list(self.targets),
            "controls": list(self.controls),
        }


@dataclass(frozen=True)
class TranspilationCertificate:
    """Carry checked endpoints and the exact rewrites connecting them."""

    source: CheckedCircuitIr
    candidate: CheckedCircuitIr
    steps: tuple[TranspilationStep, ...]
    schema_version: str = "0.2"
    equivalence: str = "exact"

    def __post_init__(self) -> None:
        """Keep unsupported equivalence notions outside the current PoC."""

        if self.schema_version != "0.2":
            raise ValueError("only transpilation certificate version '0.2' is supported")
        if self.equivalence != "exact":
            raise ValueError("only exact transpilation equivalence is supported")
        if self.source.num_qubits != self.candidate.num_qubits:
            raise ValueError("certificate endpoints require equal qubit counts")

    def to_dict(self) -> dict[str, Any]:
        """Embed both endpoint IR documents so the certificate is self-contained."""

        return {
            "schema_version": self.schema_version,
            "equivalence": self.equivalence,
            "source": checked_ir_to_dict(self.source),
            "candidate": checked_ir_to_dict(self.candidate),
            "steps": [step.to_dict() for step in self.steps],
        }


class UnsupportedTranspilationError(ValueError):
    """Report a valid transformation outside the certified rewrite catalog."""


SELF_INVERSE_GATES = frozenset(
    {GateName.X, GateName.Z, GateName.H, GateName.CNOT, GateName.SWAP}
)


def _is_self_inverse_pair(left: CheckedOperation, right: CheckedOperation) -> bool:
    """Recognize equal adjacent involutions without depending on Qiskit."""

    return left == right and left.gate in SELF_INVERSE_GATES


def certify_self_inverse_cancellations(
    source: CheckedCircuitIr,
    candidate: CheckedCircuitIr,
) -> TranspilationCertificate:
    """Certify a candidate reached by cancelling adjacent self-inverse gates."""

    if source.num_qubits != candidate.num_qubits:
        raise UnsupportedTranspilationError("transpilation changed the qubit count")

    operations = list(source.operations)
    steps: list[TranspilationStep] = []
    position = 0
    while position + 1 < len(operations):
        if _is_self_inverse_pair(operations[position], operations[position + 1]):
            operation = operations[position]
            del operations[position : position + 2]
            steps.append(
                TranspilationStep(
                    rule="cancel_self_inverse",
                    position=position,
                    gate=operation.gate,
                    targets=operation.targets,
                    controls=operation.controls,
                )
            )
            # A cancellation can expose a new pair across its left boundary.
            position = max(0, position - 1)
            continue
        position += 1

    if tuple(operations) != candidate.operations:
        raise UnsupportedTranspilationError(
            "candidate is not obtained solely by certified self-inverse cancellations"
        )
    if not steps:
        raise UnsupportedTranspilationError(
            "no certified self-inverse cancellation was found"
        )

    return TranspilationCertificate(source, candidate, tuple(steps))


def certify_h_cancellations(
    source: CheckedCircuitIr,
    candidate: CheckedCircuitIr,
) -> TranspilationCertificate:
    """Preserve the 0.1 API name while using the generalized recognizer."""

    return certify_self_inverse_cancellations(source, candidate)
