from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


class InvalidIrError(ValueError):
    """Raised when circuit IR violates the supported schema semantics."""


_SINGLE_QUBIT_GATES = frozenset({"I", "X", "Z", "H"})


def _require_index(
    value: object,
    *,
    qubits: int,
    field_name: str,
) -> int:
    """Validate one qubit index against the circuit dimension."""

    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value < qubits
    ):
        raise InvalidIrError(
            f"{field_name} must be an index in [0, {qubits})"
        )

    return value


def _require_indices(
    operation: Mapping[str, Any],
    field_name: str,
    *,
    expected_size: int,
    qubits: int,
) -> tuple[int, ...]:
    """Validate one fixed-arity operand array."""

    values = operation.get(field_name)
    if not isinstance(values, list) or len(values) != expected_size:
        raise InvalidIrError(
            f"{field_name} must contain {expected_size} index(es)"
        )

    return tuple(
        _require_index(
            value,
            qubits=qubits,
            field_name=f"{field_name}[{index}]",
        )
        for index, value in enumerate(values)
    )


def validate_ir(data: Mapping[str, Any]) -> None:
    """Validate cross-field constraints not captured reliably by JSON Schema."""

    if data.get("schema_version") != "0.1":
        raise InvalidIrError(
            "only circuit IR schema version '0.1' is supported"
        )

    qubits = data.get("qubits")
    operations = data.get("operations")

    if (
        not isinstance(qubits, int)
        or isinstance(qubits, bool)
        or qubits < 1
    ):
        raise InvalidIrError("qubits must be a positive integer")

    if not isinstance(operations, list):
        raise InvalidIrError("operations must be a JSON array")

    for index, raw_operation in enumerate(operations):
        if not isinstance(raw_operation, dict):
            raise InvalidIrError(
                f"operations[{index}] must be a JSON object"
            )

        gate = raw_operation.get("gate")
        prefix = f"operations[{index}]"

        if gate in _SINGLE_QUBIT_GATES:
            _require_indices(
                raw_operation,
                "targets",
                expected_size=1,
                qubits=qubits,
            )
        elif gate == "CNOT":
            controls = _require_indices(
                raw_operation,
                "controls",
                expected_size=1,
                qubits=qubits,
            )
            targets = _require_indices(
                raw_operation,
                "targets",
                expected_size=1,
                qubits=qubits,
            )
            if controls[0] == targets[0]:
                raise InvalidIrError(
                    f"{prefix} uses the same CNOT control and target"
                )
        elif gate == "SWAP":
            targets = _require_indices(
                raw_operation,
                "targets",
                expected_size=2,
                qubits=qubits,
            )
            if targets[0] == targets[1]:
                raise InvalidIrError(
                    f"{prefix} uses the same SWAP target twice"
                )
        else:
            raise InvalidIrError(
                f"{prefix} uses unsupported gate {gate!r}"
            )


def load_ir(path: str | Path) -> dict[str, Any]:
    """Load circuit IR and validate its semantic constraints."""

    ir_path = Path(path)
    data = json.loads(ir_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise InvalidIrError("circuit IR must be a JSON object")

    validate_ir(data)
    return data
