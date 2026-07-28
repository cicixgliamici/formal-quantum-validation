"""Deterministic serialization of checked circuit IR."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fqv.ir.checked import CheckedCircuitIr, GateName


def checked_ir_to_dict(circuit: CheckedCircuitIr) -> dict[str, Any]:
    """Return the canonical raw representation of checked IR."""

    operations: list[dict[str, Any]] = []
    for operation in circuit.operations:
        raw: dict[str, Any] = {
            "gate": operation.gate.value,
            "targets": list(operation.targets),
        }
        if operation.gate is GateName.CNOT:
            raw["controls"] = list(operation.controls)
        operations.append(raw)
    return {
        "schema_version": circuit.schema_version,
        "name": circuit.name,
        "qubits": circuit.num_qubits,
        "operations": operations,
    }


def write_checked_ir(
    circuit: CheckedCircuitIr,
    destination: str | Path,
) -> Path:
    """Write canonical checked IR as UTF-8 JSON."""

    output = Path(destination)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            checked_ir_to_dict(circuit),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return output
