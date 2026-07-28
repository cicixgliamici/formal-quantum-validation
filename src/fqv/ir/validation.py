"""Validate raw IR and construct its checked representation."""

from __future__ import annotations

from typing import Any, Mapping

from fqv.ir.checked import (
    CheckedCircuitIr,
    CheckedOperation,
    GateName,
)


class InvalidIrError(ValueError):
    """Raised before malformed raw IR can become a checked circuit.

    The exception reports structural invalidity. It does not mean that a
    structurally valid circuit satisfies its quantum contract.
    """


def _index(value: object, *, qubits: int, field_name: str) -> int:
    """Accept an integer only when it denotes an existing logical qubit."""
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value < qubits
    ):
        raise InvalidIrError(
            f"{field_name} must be an index in [0, {qubits})"
        )
    return value


def _indices(
    operation: Mapping[str, Any],
    field_name: str,
    *,
    size: int,
    qubits: int,
) -> tuple[int, ...]:
    """Validate a fixed-arity operand array and freeze its order."""
    values = operation.get(field_name)
    if not isinstance(values, list) or len(values) != size:
        raise InvalidIrError(
            f"{field_name} must contain {size} index(es)"
        )
    return tuple(
        _index(
            value,
            qubits=qubits,
            field_name=f"{field_name}[{position}]",
        )
        for position, value in enumerate(values)
    )


def _operation(
    raw: object,
    *,
    position: int,
    qubits: int,
) -> CheckedOperation:
    """Validate one raw operation using gate-specific arity rules."""
    if not isinstance(raw, dict):
        raise InvalidIrError(
            f"operations[{position}] must be a JSON object"
        )

    prefix = f"operations[{position}]"
    gate_value = raw.get("gate")
    # Converting to GateName closes the external string vocabulary. All code
    # below can therefore treat the remaining cases exhaustively.
    try:
        gate = GateName(gate_value)
    except (TypeError, ValueError) as error:
        raise InvalidIrError(
            f"{prefix} uses unsupported gate {gate_value!r}"
        ) from error

    # Single-qubit gates share the same shape and need no control operands.
    if gate in {
        GateName.IDENTITY,
        GateName.X,
        GateName.Z,
        GateName.H,
    }:
        return CheckedOperation(
            gate=gate,
            targets=_indices(
                raw,
                "targets",
                size=1,
                qubits=qubits,
            ),
        )
    # CNOT has two roles, not merely two unordered operands. Keeping controls
    # and targets distinct avoids losing semantics during backend translation.
    if gate is GateName.CNOT:
        controls = _indices(
            raw,
            "controls",
            size=1,
            qubits=qubits,
        )
        targets = _indices(
            raw,
            "targets",
            size=1,
            qubits=qubits,
        )
        if controls[0] == targets[0]:
            raise InvalidIrError(
                f"{prefix} uses the same CNOT control and target"
            )
        return CheckedOperation(
            gate=gate,
            controls=controls,
            targets=targets,
        )

    # SWAP is the only remaining GateName in schema 0.1.
    targets = _indices(
        raw,
        "targets",
        size=2,
        qubits=qubits,
    )
    if targets[0] == targets[1]:
        raise InvalidIrError(
            f"{prefix} uses the same SWAP target twice"
        )
    return CheckedOperation(gate=gate, targets=targets)


def check_ir(data: Mapping[str, Any]) -> CheckedCircuitIr:
    """Turn untrusted raw IR into the representation accepted later.

    Successful construction proves schema version, circuit dimension, gate
    vocabulary, arity, index bounds, and distinct two-qubit operands. It does
    not yet prove the future linear-resource judgment described in the
    research roadmap.
    """

    if data.get("schema_version") != "0.1":
        raise InvalidIrError(
            "only circuit IR schema version '0.1' is supported"
        )
    name = data.get("name")
    qubits = data.get("qubits")
    operations = data.get("operations")
    if not isinstance(name, str) or not name:
        raise InvalidIrError("name must be a non-empty string")
    if (
        not isinstance(qubits, int)
        or isinstance(qubits, bool)
        or qubits < 1
    ):
        raise InvalidIrError("qubits must be a positive integer")
    if not isinstance(operations, list):
        raise InvalidIrError("operations must be a JSON array")

    # Preserve source order exactly: circuit lists are execution ordered, and
    # even a permutation of individually valid operations may change meaning.
    return CheckedCircuitIr(
        schema_version="0.1",
        name=name,
        num_qubits=qubits,
        operations=tuple(
            _operation(raw, position=index, qubits=qubits)
            for index, raw in enumerate(operations)
        ),
    )
