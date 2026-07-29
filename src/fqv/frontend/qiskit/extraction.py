"""Extract restricted circuit IR from Qiskit circuits.

Circuit builders, the verification CLI, and the transpilation path call this
module when a Qiskit circuit must cross back into the shared representation.
The resulting JSON is consumed next by ``ir.validation`` or by external tools;
unsupported Qiskit features stop here instead of leaking into core IR.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qiskit import QuantumCircuit


class UnsupportedCircuitError(ValueError):
    """Raised when Qiskit data cannot be represented without information loss.

    Failing closed is intentional. Silently dropping measurement, classical
    operands, or gate parameters would produce an IR with different semantics.
    """


_SINGLE_QUBIT_GATES = {
    "id": "I",
    "x": "X",
    "z": "Z",
    "h": "H",
}


def circuit_to_ir(circuit: QuantumCircuit) -> dict[str, Any]:
    """Extract a JSON-compatible, execution-ordered restricted IR.

    Qiskit qubit positions are converted to integer logical indices here. This
    frontend is therefore part of the bit-ordering trust boundary.
    """

    operations: list[dict[str, Any]] = []
    for instruction in circuit.data:
        operation = instruction.operation
        gate_name = operation.name
        qubits = [
            circuit.find_bit(qubit).index
            for qubit in instruction.qubits
        ]
        # IR 0.1 has no exact parameter language. Rejecting parameters avoids
        # silently rounding or erasing rotation semantics.
        if operation.params:
            raise UnsupportedCircuitError(
                f"Parameterized operation {gate_name!r} is outside IR 0.1"
            )
        if instruction.clbits:
            raise UnsupportedCircuitError(
                f"Classical operands in {gate_name!r} are outside IR 0.1"
            )
        if gate_name in _SINGLE_QUBIT_GATES:
            if len(qubits) != 1:
                raise UnsupportedCircuitError(
                    f"Gate {gate_name!r} requires one target"
                )
            operations.append(
                {
                    "gate": _SINGLE_QUBIT_GATES[gate_name],
                    "targets": qubits,
                }
            )
        elif gate_name == "cx":
            if len(qubits) != 2:
                raise UnsupportedCircuitError(
                    "CNOT requires one control and one target"
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
                raise UnsupportedCircuitError("SWAP requires two targets")
            operations.append({"gate": "SWAP", "targets": qubits})
        # Barriers affect scheduling but not the ideal unitary denotation, so
        # IR 0.1 documents and implements an explicit erase policy for them.
        elif gate_name != "barrier":
            raise UnsupportedCircuitError(
                f"Operation {gate_name!r} is outside IR 0.1"
            )
    return {
        "schema_version": "0.1",
        "name": circuit.name or "unnamed",
        "qubits": circuit.num_qubits,
        "operations": operations,
    }


def export_ir(circuit: QuantumCircuit, destination: str | Path) -> Path:
    """Export deterministic restricted circuit IR."""

    output = Path(destination)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(circuit_to_ir(circuit), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output
