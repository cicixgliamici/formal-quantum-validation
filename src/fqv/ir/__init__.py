"""Raw and checked circuit IR boundary."""

from fqv.ir.checked import (
    CheckedCircuitIr,
    CheckedOperation,
    GateName,
)
from fqv.ir.raw import RawCircuitIr, RawOperation, load_raw_ir
from fqv.ir.serialization import checked_ir_to_dict, write_checked_ir
from fqv.ir.validation import InvalidIrError, check_ir


def circuit_to_ir(circuit):
    """Compatibility adapter for the former Qiskit-facing IR module."""

    from fqv.frontend.qiskit.extraction import circuit_to_ir as extract

    return extract(circuit)


def export_ir(circuit, destination):
    """Compatibility adapter for deterministic Qiskit IR export."""

    from fqv.frontend.qiskit.extraction import export_ir as export

    return export(circuit, destination)


__all__ = [
    "CheckedCircuitIr",
    "CheckedOperation",
    "GateName",
    "InvalidIrError",
    "RawCircuitIr",
    "RawOperation",
    "check_ir",
    "checked_ir_to_dict",
    "circuit_to_ir",
    "export_ir",
    "load_raw_ir",
    "write_checked_ir",
]
