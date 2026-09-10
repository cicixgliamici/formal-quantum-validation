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
    """One operation with checked gate, arity, and non-negative operands.

    The current checked model preserves sequential execution order but is not
    yet the planned resource-linear SSA representation. Calling this object
    `CheckedOperation` means structural safety only; it does not claim
    semantic correctness or no-aliasing across a future graph IR.

    ir.validation._operation builds this from a raw operation dictionary.
    __post_init__ checks invariants that need no register size; the containing
    CheckedCircuitIr checks upper index bounds. For CNOT, controls[0] is the
    condition qubit and targets[0] is the qubit that may flip. Conversion to
    Qiskit and formatting for Lean must preserve those distinct roles.
    """

    gate: GateName
    targets: tuple[int, ...]
    controls: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        """Keep direct Python construction as safe as parsed construction."""
        if not isinstance(self.gate, GateName):
            raise ValueError("gate must be a GateName")
        target_count = 2 if self.gate is GateName.SWAP else 1
        control_count = 1 if self.gate is GateName.CNOT else 0
        for name, operands, count in (
            ("targets", self.targets, target_count),
            ("controls", self.controls, control_count),
        ):
            if not isinstance(operands, tuple) or len(operands) != count:
                raise ValueError(f"{name} must be a tuple of {count} indices")
            if any(type(index) is not int or index < 0 for index in operands):
                raise ValueError(f"{name} require non-negative integer indices")
        operands = self.targets + self.controls
        if len(set(operands)) != len(operands):
            raise ValueError("gate operands must be distinct")


@dataclass(frozen=True)
class CheckedCircuitIr:
    """Immutable circuit accepted by the structural IR boundary.

    Operations are stored in a tuple because reordering after validation would
    change circuit semantics. Immutability also makes this value suitable as
    the input to future lowering and certificate-generation stages.

    Data path: load_raw_ir -> check_ir -> CheckedCircuitIr. The executable
    path consumes it in checked_ir_to_qiskit; the formal path consumes its
    operations in generate_lean_module. Serialization can return it to JSON,
    but that JSON must cross check_ir again when read as external input.
    Structural validity alone says nothing about the desired output state.
    """

    schema_version: str
    name: str
    num_qubits: int
    operations: tuple[CheckedOperation, ...]

    def __post_init__(self) -> None:
        """Validate register-dependent bounds and prevent mutable operations."""
        if self.schema_version != "0.1":
            raise ValueError("only circuit IR schema version '0.1' is supported")
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("name must be a non-empty string")
        if type(self.num_qubits) is not int or self.num_qubits < 1:
            raise ValueError("num_qubits must be a positive integer")
        if not isinstance(self.operations, tuple):
            raise ValueError("operations must be an immutable tuple")
        for operation in self.operations:
            if not isinstance(operation, CheckedOperation):
                raise ValueError("operations must contain CheckedOperation values")
            if any(index >= self.num_qubits
                   for index in operation.targets + operation.controls):
                raise ValueError("gate operand is outside the circuit register")
