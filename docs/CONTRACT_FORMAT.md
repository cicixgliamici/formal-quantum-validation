# Shared contract format

Contract schema version `0.1` is the single semantic specification consumed by
the executable Python checker and the Lean and Coq module generators.

The canonical Bell example is distributed at
`src/fqv/data/bell.contract.json`. The matching circuit IR is
`examples/bell_ir.json`.

## Exact amplitudes

States use symbolic tokens instead of decimal approximations:

- `zero`
- `one` and `minus_one`
- `i` and `minus_i`
- `inv_sqrt_two` and `minus_inv_sqrt_two`

Python interprets these tokens as complex numbers for simulation. Lean and Coq
map the same tokens to exact expressions in their respective libraries. This
prevents a decimal approximation from becoming a formal theorem statement.

Each state must contain exactly `2 ^ qubits` amplitudes. Version `0.1` does not
yet provide a general expression language for arbitrary algebraic amplitudes.
Both states must be normalized. The parser allows at most `1e-12` absolute
roundoff error in the squared norm; it never rescales the supplied state.
Unknown fields and non-finite tolerances are rejected.

## Equality and global phase

The target denotes an exact vector, including global phase, as in both generated
formal equalities. Python checks amplitude agreement with absolute tolerance
`1e-12` and additionally enforces `fidelity_threshold`. Fidelity alone is
insufficient: vectors differing only by global phase have fidelity one but fail
this contract.

The separate transpilation report explicitly compares operators *up to global
phase*. Passing that numerical comparison does not establish the exact-vector
contract and does not guarantee that the transpiled circuit can be exported.
IR 0.1 export rejects nonzero or symbolic stored global phase and attached
layouts because neither can be preserved by the current representation.

## Contract sections

- `initial_state` is the executable precondition.
- `target_state` is the exact state-preparation postcondition.
- `fidelity_threshold` controls the executable ideal-state comparison.
- `probabilities` define computational-basis observations.
- `resources` describe gate inventory constraints on the logical circuit.

Resource constraints are not part of the generated Lean or Coq
state-correctness theorem. They remain executable structural checks because
transpilation may change them without changing circuit semantics.

## Specification, numerical check, and formal contract

These terms describe different artifacts and must not be used interchangeably:

1. The JSON contract is a declarative specification. It records the expected
   precondition, postcondition, observations, and resource constraints. Merely
   writing or validating this document does not establish that a circuit
   satisfies it.
2. `fqv-verify` performs an executable numerical check. Qiskit computes the
   ideal output for the one declared `initial_state`; Python compares floating-
   point amplitudes, fidelity, probabilities, samples, and resources with the
   declared expectations. A `PASS` is reproducible evidence for that execution
   and those tolerances, but it depends on Python, Qiskit, NumPy, and the
   implementation of the checker.
3. A generated and compiled Lean or Coq theorem is a formal satisfaction proof
   for the exact statement emitted from the contract. Symbolic amplitudes are
   mapped to mathematical expressions, and the proof assistant's kernel checks
   the proof term. This removes floating-point tolerance from the theorem, but
   the extractor and generator remain trusted to translate the source artifacts
   faithfully.

The project therefore uses a real contract as a specification in both paths,
but only kernel acceptance turns the supported semantic part of that contract
into a machine-checked theorem. Resource limits, sampled probabilities, and the
Python fidelity threshold remain executable checks; they are not currently
included in the generated theorem.

For the state-correctness fragment, the distinction can be summarized as:

```text
Numerical evidence:  simulate(C, psi) approximately equals phi
Formal statement:    denote(C)(psi) = phi
Formal evidence:     a kernel-checked proof of that equality
```

Here `psi` is the exact `initial_state`, `phi` is the exact `target_state`, and
`denote` is the formal circuit semantics. The current generated theorem covers
that declared input exactly; it is not a universal claim about every possible
input unless the theorem explicitly quantifies over all states, as the
transpilation-equivalence theorem does.

## Curry-Howard correspondence

The Curry-Howard correspondence reads propositions as types and proofs as
terms inhabiting those types. In this project, the generated Lean or Coq
equality is a proposition. The generated proof script asks the proof assistant
to construct a term of that type, and the small trusted kernel checks the term.
If no valid term can be constructed, the contract obligation is not accepted.

This explains why source generation alone is not proof. A `.lean` or `.v` file
contains a proposed proposition and proof construction; successful kernel
checking supplies the formal evidence. Curry-Howard does not itself prove that
Python translated the JSON correctly, so generator drift tests and semantic
regressions address a separate trust-boundary concern.

## Hoare logic interpretation

Classical program contracts are commonly written as a Hoare triple:

```text
{ P } C { Q }
```

It means that when precondition `P` holds, executing command `C` establishes
postcondition `Q`, subject to the chosen partial- or total-correctness
interpretation. The current pure-state contract has the analogous shape:

```text
{ state = psi } circuit { state = phi }
```

The analogy is useful but deliberately narrow. `initial_state` fixes one exact
input vector rather than describing an arbitrary set of permitted states, and
`target_state` fixes one exact output vector. The generated theorem proves this
state transformation for a finite unitary circuit. It does not yet provide a
general assertion language, loops, classical control, or termination rules.

Quantum Hoare logics generalize preconditions and postconditions to quantum
predicates, often represented as projectors or positive operators (effects),
and typically interpret programs over density operators. Such a judgment can
express subspaces, mixed states, measurement branches, and probabilistic
properties without fixing one state vector. More expressive systems also
distinguish partial from total correctness and define rules for measurement,
initialization, classical control, and loops.

This repository does not claim to implement a full Quantum Hoare Logic. Its
version `0.1` contract and formal backends cover finite pure states, exact
unitary circuits, and concrete state equalities. The general Lean preservation
theorems and the all-input `H; H` circuit equivalence go beyond one fixed
pre/post example, but they still use direct denotational equality rather than a
quantum-predicate proof calculus. A future contract language based on quantum
predicates could turn the present pre/post discipline into a genuine QHL-style
system for measurements, mixed states, and branching programs.

## Generating formal obligations

From an installed development environment:

```powershell
fqv-generate --backend lean `
  examples/bell_ir.json `
  src/fqv/data/bell.contract.json `
  lean/QuantumValidation/GeneratedBell.lean

lake build
```

Generation performs these checks before writing a module:

1. IR schema version and gate operands are valid.
2. Contract schema version and state dimensions are valid.
3. Circuit and contract declare the same number of qubits.
4. Every gate is supported by the general finite Lean semantics.

The same command supports the three-qubit GHZ example:

```powershell
fqv-generate --backend lean `
  examples/ghz3_ir.json `
  src/fqv/data/ghz3.contract.json `
  lean/QuantumValidation/GeneratedGhz3.lean
```

Select the Coq backend and a `.v` destination to generate the corresponding
SQIR obligation:

```powershell
fqv-generate --backend coq `
  examples/dj2_balanced_ir.json `
  src/fqv/data/dj2_balanced.contract.json `
  coq/QuantumValidation/GeneratedDj2Balanced.v
```

The generated proof enumerates computational-basis assignments. This is clear
and effective for small review cases, but its size grows exponentially with
the number of qubits. Larger parametric proofs will require reusable lemmas
instead of enumeration.

Generated Lean and Coq modules should be reviewed as derived evidence. Editing
them by hand would break traceability to the source IR and contract.

## Relationship to transpilation certificates

A state contract specifies one input/output behavior. The adjacent `H; H`
certificate instead proves that two checked circuits have the same behavior
for every input. Its JSON artifact therefore stores source IR, candidate IR,
and rewrite steps rather than extending the contract schema. Both endpoints
must still satisfy the normal IR validation rules. See
[transpilation validation](TRANSPILATION_VALIDATION.md#exact-rewrite-certificate).
