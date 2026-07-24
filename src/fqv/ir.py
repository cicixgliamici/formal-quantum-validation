from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qiskit import QuantumCircuit


class UnsupportedCircuitError(ValueError):
    """Raised when a circuit is outside the MVP 0 fragment."""


_SINGLE_QUBIT_GATES: dict[str, str] = {
    "id": "I",
    "x": "X",
    "z": "Z",
    "h": "H",
}


def circuit_to_ir(
    circuit: QuantumCircuit,
) -> dict[str, Any]:
    """Extract a restricted JSON-compatible circuit IR.

    Supported operations:
    - I
    - X
    - Z
    - H
    - CNOT
    - SWAP

    Unsupported:
    - measurements
    - reset
    - classical control
    - parameters
    - arbitrary custom gates
    """

    operations: list[dict[str, Any]] = []

    for instruction in circuit.data:
        operation = instruction.operation
        gate_name = operation.name

        qubits = [
            circuit.find_bit(qubit).index
            for qubit in instruction.qubits
        ]

        if operation.params:
            raise UnsupportedCircuitError(
                f"Parameterized operation {gate_name!r} "
                "is outside MVP 0"
            )

        if instruction.clbits:
            raise UnsupportedCircuitError(
                f"Classical operands in {gate_name!r} "
                "are outside MVP 0"
            )

        if gate_name in _SINGLE_QUBIT_GATES:
            if len(qubits) != 1:
                raise UnsupportedCircuitError(
                    f"Gate {gate_name!r} should have "
                    f"one target, observed {qubits}"
                )

            operations.append(
                {
                    "gate": _SINGLE_QUBIT_GATES[
                        gate_name
                    ],
                    "targets": qubits,
                }
            )

        elif gate_name == "cx":
            if len(qubits) != 2:
                raise UnsupportedCircuitError(
                    "CNOT requires one control "
                    "and one target"
                )

            operations.append(
                {
                    "gate": "CNOT",
                    "controls": [qubits[0]],
                    "targets": [qubits[1]],
                }
            )

        elif gate_name == "swap":
            if len(qubits) != 2:
                raise UnsupportedCircuitError(
                    "SWAP requires two targets"
                )

            operations.append(
                {
                    "gate": "SWAP",
                    "targets": qubits,
                }
            )

        elif gate_name == "barrier":
            continue

        else:
            raise UnsupportedCircuitError(
                f"Operation {gate_name!r} "
                "is outside the MVP 0 fragment"
            )

    return {
        "schema_version": "0.1",
        "name": circuit.name or "unnamed",
        "qubits": circuit.num_qubits,
        "operations": operations,
    }


def export_ir(
    circuit: QuantumCircuit,
    destination: str | Path,
) -> Path:
    """Export a circuit using the restricted JSON IR."""

    output_path = Path(destination)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ir = circuit_to_ir(circuit)

    output_path.write_text(
        json.dumps(
            ir,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return output_path
