"""Immutable, validated circuit IR used past the input boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class GateName(StrEnum):
    """Closed gate vocabulary supported by IR schema version 0.1.

    Converting an external string to this enum is the first step that removes
    ambiguity from raw JSON. Later stages can exhaustively branch on the enum
    instead of handling arbitrary provider-specific names.
    """

    IDENTITY = "I"
    X = "X"
    Z = "Z"
    H = "H"
    CNOT = "CNOT"
    SWAP = "SWAP"


@dataclass(frozen=True)
class CheckedOperation:
    """One operation whose gate, arity, and operand bounds were checked.

    The current checked model preserves sequential execution order but is not
    yet the planned resource-linear SSA representation. Calling this object
    `CheckedOperation` means structural safety only; it does not claim
    semantic correctness or no-aliasing across a future graph IR.
    """

    gate: GateName
    targets: tuple[int, ...]
    controls: tuple[int, ...] = ()


@dataclass(frozen=True)
class CheckedCircuitIr:
    """Immutable circuit accepted by the structural IR boundary.

    Operations are stored in a tuple because reordering after validation would
    change circuit semantics. Immutability also makes this value suitable as
    the input to future lowering and certificate-generation stages.
    """

    schema_version: str
    name: str
    num_qubits: int
    operations: tuple[CheckedOperation, ...]
