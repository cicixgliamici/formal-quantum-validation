# Circuit IR conventions

The circuit IR is the explicit boundary between Qiskit extraction and the
future Lean semantics. Version `0.1` supports only finite unitary circuits.

## Supported fragment

- One or more qubits
- Gates `I`, `X`, `Z`, `H`, `CNOT`, and `SWAP`
- No gate parameters
- No measurements, resets, classical operands, or classical control
- Barriers are discarded because they have no unitary semantics

Unsupported operations must cause extraction to fail. They must never be
silently approximated or omitted.

## Ordering

Operations are stored in Qiskit execution order. The first array element is
applied first. A formal denotation must therefore compose matrices in the
corresponding mathematical order.

Qubit indices follow Qiskit's little-endian convention. For two qubits, the
statevector basis order is `|00>`, `|01>`, `|10>`, `|11>`, where qubit zero is
the least significant bit. The Lean semantics must document and test the same
choice.

## Gate operands

- A single-qubit gate has exactly one target.
- `CNOT` has exactly one control and one target.
- `SWAP` has exactly two targets.
- Every operand must be smaller than the top-level `qubits` value.
- Control and target operands of the same operation must be distinct.

JSON Schema validates shape and non-negative indices. Cross-field constraints,
including index bounds and distinct operands, must also be checked by the IR
loader because JSON Schema cannot express them clearly in this representation.

## Canonical serialization

Exporters use UTF-8, two-space indentation, lexicographically sorted object
keys, and one final newline. Canonical output makes reviews and regression
tests deterministic.

## Semantic scope

Version `0.1` does not encode an initial state, expected output, global phase,
resource bound, or measurement property. Those belong to a separate contract
format. Keeping circuits and specifications separate prevents structural data
from being mistaken for a correctness claim.
