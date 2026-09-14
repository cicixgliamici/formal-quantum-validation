# Circuit IR conventions

The circuit IR is the explicit boundary between Qiskit extraction and the
Lean and Coq/SQIR semantics. Version `0.1` supports only finite unitary circuits.

## Supported fragment

- One or more qubits
- Gates `I`, `X`, `Z`, `H`, `CNOT`, and `SWAP`
- No gate parameters
- No measurements, resets, classical operands, or classical control
- Barriers are discarded because they have no unitary semantics

Unsupported operations must cause extraction to fail. They must never be
silently approximated or omitted.
Nonzero or symbolic stored global phase and attached transpiler layouts are
also rejected. Exact export requires an explicit representation or logical
remapping for these features. Unknown JSON fields are rejected at every level.

## Ordering

Operations are stored in Qiskit execution order. The first array element is
applied first. A formal denotation must therefore compose matrices in the
corresponding mathematical order.

Qubit indices follow Qiskit's little-endian convention. For two qubits, the
statevector basis order is `|00>`, `|01>`, `|10>`, `|11>`, where qubit zero is
the least significant bit. Both formal backends document and test the same
choice; the Coq serializer writes bit `k` in QuantumLib ket position `k`.

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

Version `0.1` does not encode an initial state, expected output, resource bound,
or measurement property. Those belong to a separate contract format. A stored
global phase is unsupported, rather than being transferred to the contract.
Keeping circuits and specifications separate prevents structural data from
being mistaken for a correctness claim.

## Transpilation certificate endpoints

The exact self-inverse rewrite certificate embeds source and candidate IR using
these same conventions. Both are validated independently before certificate
recognition. Each `cancel_self_inverse` step identifies the position, gate,
targets, and controls of one adjacent equal pair; deterministic replay must
reconstruct the candidate exactly. Certificate schema `0.2` adds this
transformation provenance without extending circuit IR version `0.1` or
weakening its export rules.
