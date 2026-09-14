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

This document describes the native Lean model. The independent lowering to
SQIR and its Coq well-typedness result are documented in
[Coq and SQIR semantics](COQ_SQIR.md).

## Lean syntax used in this project

The formalization uses a compact subset of Lean:

- `abbrev` introduces a transparent abbreviation. `Basis n` means
  `Fin n -> Bool`, and `State n` means a function from basis assignments to
  complex amplitudes.
- `def` introduces a definition, while `noncomputable def` marks a mathematical
  definition that Lean is not expected to compile into executable code. Exact
  square roots and complex amplitudes require this distinction.
- `inductive Gate` declares the supported gate syntax. Its constructors carry
  operands and, for CNOT/SWAP, a proof that the two operands differ.
- `Fin n` is the type of natural numbers smaller than `n`. Using it for qubit
  operands makes an out-of-range formal gate unrepresentable.
- `fun basis => ...` defines a function, and `match` or `if` selects its value
  by cases. States are functions, so circuit semantics ultimately computes one
  amplitude for each `basis`.
- `theorem name : proposition := by ...` states a proposition and begins a
  tactic proof. Lean accepts the declaration only after its kernel validates
  the constructed proof term.
- `@[simp]` registers a proved equality for controlled simplification. `simp`
  then rewrites with definitions and such lemmas; it does not bypass proof
  checking.
- `funext` reduces equality of two state functions to pointwise equality;
  `induction` proves a statement for every recursively constructed size or
  list; `rfl` closes definitional equalities; `rw` applies proved equalities.
- Terms such as `(by decide)` are proofs produced by a decision procedure, for
  example that two concrete qubit indices differ. The resulting proof term is
  still checked by the kernel.

The key semantic functions are `Gate.apply`, which maps one input state to the
state after one gate, and `denote`, which uses `List.foldl` to apply every gate
from left to right. Reading generated correctness theorems as
`denote circuit input = target` is enough to understand their main claim.

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

This fixed circuit uses a **CNOT chain**:

```text
H(0); CNOT(0, 1); CNOT(1, 2)
```

Its circuit, eight input amplitudes, eight target amplitudes, and theorem are
generated mechanically from JSON. The proof establishes function equality by
examining all `2^3` basis assignments. This makes GHZ(3) a concrete end-to-end
regression for IR validation, generation, bit ordering, and gate semantics.

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

The distinction is therefore both structural and proof-theoretic:

| Aspect | Fixed GHZ(3) | Parametric GHZ(n) |
| --- | --- | --- |
| Circuit topology | Chain: `0 -> 1 -> 2` | Fan-out: `0 -> 1, 0 -> 2, ..., 0 -> n-1` |
| Source | Generated from IR and contract JSON | Written as reusable Lean definitions |
| Register size | Exactly three qubits | Every nonempty finite `n` |
| Proof method | Enumerates all eight basis assignments | Induction over the fan-out gates |
| Main purpose | End-to-end generator regression | Universal mathematical family theorem |

Both topologies prepare the same GHZ state from the all-zero input. GHZ(3) is
not merely the `n = 3` file emitted from `ghzCircuit`: it intentionally uses a
different CNOT arrangement. Lean also derives `ghz_three_correct` by setting
`n = 3` in the parametric theorem, so the repository contains two independent
routes to a three-qubit GHZ result.

The main parametric definitions and lemmas form a short proof pipeline:

- `prefixBasis count` describes the basis assignment whose first `count`
  qubits are one;
- `ket assignment` constructs the basis state concentrated at that assignment;
- `ghzPrefix count` states the invariant after entangling a prefix;
- `ghzFanout` recursively builds CNOTs from qubit zero;
- `hadamard_zero_starts_ghz` establishes the first two-branch superposition;
- `fanoutGate_advances` proves one inductive step;
- `ghzFanout_correct` repeats that step by induction;
- `ghz_correct` combines the Hadamard base case with the complete fan-out.

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

## Hadamard cancellation

`lean/QuantumValidation/Transpilation.lean` proves `h_apply_twice`: applying
Hadamard twice on any valid target returns every finite state unchanged. The
derived `duplicate_h_transpilation_correct` theorem lifts this identity to
`CircuitEquivalent [.h target, .h target] []`, which quantifies over every
input state and every register size for which the target exists.

Generated transpilation obligations instantiate this result only after the
certificate trace has been replayed against its checked source and candidate
IR. This proves the accepted `H; H` rewrite, not other Qiskit optimizations.
