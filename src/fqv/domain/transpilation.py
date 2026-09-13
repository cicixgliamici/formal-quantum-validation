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
    target: int

    def to_dict(self) -> dict[str, Any]:
        """Return the stable JSON representation shared by formal backends."""

        return {
            "rule": self.rule,
            "position": self.position,
            "target": self.target,
        }


@dataclass(frozen=True)
class TranspilationCertificate:
    """Carry checked endpoints and the exact rewrites connecting them."""

    source: CheckedCircuitIr
    candidate: CheckedCircuitIr
    steps: tuple[TranspilationStep, ...]
    schema_version: str = "0.1"
    equivalence: str = "exact"

    def __post_init__(self) -> None:
        """Keep unsupported equivalence notions outside the current PoC."""

        if self.schema_version != "0.1":
            raise ValueError("only transpilation certificate version '0.1' is supported")
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


def _is_duplicate_h(left: CheckedOperation, right: CheckedOperation) -> bool:
    """Recognize the first exact rule without depending on Qiskit objects."""

    return (
        left.gate is GateName.H
        and right.gate is GateName.H
        and left.targets == right.targets
    )


def certify_h_cancellations(
    source: CheckedCircuitIr,
    candidate: CheckedCircuitIr,
) -> TranspilationCertificate:
    """Build a certificate when leftmost `H; H` cancellation reaches candidate."""

    if source.num_qubits != candidate.num_qubits:
        raise UnsupportedTranspilationError("transpilation changed the qubit count")

    operations = list(source.operations)
    steps: list[TranspilationStep] = []
    position = 0
    while position + 1 < len(operations):
        if _is_duplicate_h(operations[position], operations[position + 1]):
            target = operations[position].targets[0]
            del operations[position : position + 2]
            steps.append(TranspilationStep("cancel_h_h", position, target))
            # A cancellation can expose a new pair across its left boundary.
            position = max(0, position - 1)
            continue
        position += 1

    if tuple(operations) != candidate.operations:
        raise UnsupportedTranspilationError(
            "candidate is not obtained solely by certified H; H cancellations"
        )
    if not steps:
        raise UnsupportedTranspilationError("no certified H; H cancellation was found")

    return TranspilationCertificate(source, candidate, tuple(steps))
