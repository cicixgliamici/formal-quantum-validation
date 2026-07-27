# General finite quantum semantics

The formal model supports a register with an arbitrary finite number `n` of
qubits:

```lean
abbrev Basis (n : Nat) := Fin n -> Bool
abbrev State (n : Nat) := Basis n -> Complex
```

A basis assignment maps every qubit position to its Boolean value. Position
zero is the least significant Qiskit qubit. A state maps each complete basis
assignment to one complex amplitude.

## Gate operands

Single-qubit gates accept a target in `Fin n`. CNOT and SWAP additionally carry
a Lean proof that their operands are distinct:

```lean
Gate.cnot control target distinct
Gate.swap left right distinct
```

Consequently, an out-of-range index or repeated operand cannot appear in a
well-typed formal circuit. Python performs the corresponding checks before
generating Lean.

## Gate semantics

- `X` reads the amplitude at the basis with its target bit flipped.
- `Z` negates amplitudes whose target bit is true.
- `H` combines amplitudes from target-bit zero and one using `1 / sqrt(2)`.
- `CNOT` flips its target whenever the control bit is true.
- `SWAP` exchanges two bit values.

Circuits remain execution-ordered gate lists and are interpreted from left to
right, matching circuit IR.

## Bell regression

The Bell contract is regenerated against the general semantics with
`Circuit 2` and `State 2`. The previous concrete two-qubit theorem remains as
an independent regression baseline.

## GHZ(3) case study

The new case study formalizes:

```text
H(0)
CNOT(0, 1)
CNOT(1, 2)
```

and checks:

```text
|000> -> (|000> + |111>) / sqrt(2)
```

The circuit, input, target, and theorem are generated from
`examples/ghz3_ir.json` and `src/fqv/data/ghz3.contract.json`. Lean checks the
resulting theorem without `sorry`.

## Remaining proof work

The representation is general in `n`, but generated example proofs currently
enumerate every basis assignment. This is appropriate for Bell and GHZ(3),
while proofs for circuit families such as GHZ(n) need algebraic lemmas and
induction.

Identity preservation and involutivity of `X`, `Z`, and valid `CNOT` gates are
proved for every register size and state. These reusable laws are the first
algebraic layer above the raw semantics.

Full unitarity and normalization preservation are not yet proved generically.
Those theorems, including Hadamard and SWAP laws, are the next formal
strengthening of this model.
