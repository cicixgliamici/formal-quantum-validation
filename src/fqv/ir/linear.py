"""Linear operation stream exposed to execution and formal backends."""

from __future__ import annotations

from collections.abc import Iterator

from fqv.ir.checked import CheckedCircuitIr, CheckedOperation


def linear_operations(
    circuit: CheckedCircuitIr,
) -> Iterator[CheckedOperation]:
    """Yield operations exactly once in declared execution order."""

    yield from circuit.operations
