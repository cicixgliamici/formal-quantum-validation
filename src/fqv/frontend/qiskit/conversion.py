"""Build Qiskit circuits from checked core IR."""

from __future__ import annotations

from qiskit import QuantumCircuit

from fqv.ir.checked import CheckedCircuitIr, GateName
from fqv.ir.linear import linear_operations


def checked_ir_to_qiskit(circuit: CheckedCircuitIr) -> QuantumCircuit:
    """Translate checked sequential IR without reinterpreting raw JSON.

    This adapter is deliberately mechanical: validation belongs to the IR
    layer, while provider-specific gate construction belongs here. Keeping the
    mapping small makes bit ordering and gate-name decisions reviewable.
    """

    result = QuantumCircuit(circuit.num_qubits, name=circuit.name)
    # `linear_operations` preserves the tuple order. Qiskit appends each gate,
    # so the produced circuit has the same left-to-right execution sequence.
    for operation in linear_operations(circuit):
        target = operation.targets[0]
        if operation.gate is GateName.IDENTITY:
            result.id(target)
        elif operation.gate is GateName.X:
            result.x(target)
        elif operation.gate is GateName.Z:
            result.z(target)
        elif operation.gate is GateName.H:
            result.h(target)
        elif operation.gate is GateName.CNOT:
            result.cx(operation.controls[0], target)
        elif operation.gate is GateName.SWAP:
            result.swap(operation.targets[0], operation.targets[1])
    return result
