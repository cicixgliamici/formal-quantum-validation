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

## Parametric GHZ family

The formal development also defines `ghzCircuit n` for every `n > 0`. It uses
`H(0)` followed by a fan-out of CNOT gates from qubit zero to every remaining
qubit. Lean proves one parametric theorem:

```text
|0...0> -> (|0...0> + |1...1>) / sqrt(2)
```

The proof is inductive in the number of fan-out gates. It does not enumerate
the `2^n` basis assignments. Qiskit contains the matching parametric circuit
constructor, while the original GHZ(3) CNOT chain remains an independent
fixed-size regression.

## Remaining proof work

The representation is general in `n`, but generated example proofs currently
enumerate every basis assignment. This is appropriate for Bell and GHZ(3),
while new generated circuit families still need dedicated algebraic invariants
and induction.

Identity preservation and involutivity of `X`, `Z`, and valid `CNOT` gates are
proved for every register size and state. In addition, every supported gate
preserves the finite complex inner product. This includes Hadamard and SWAP,
not only the basis-permutation gates.

The formal squared norm is the real part of the self-inner-product. Lean proves
that every supported gate and every supported circuit preserves this norm.
Consequently, a circuit maps every normalized input state to a normalized
output state.
