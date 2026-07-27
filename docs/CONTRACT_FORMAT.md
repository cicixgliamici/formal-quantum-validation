# Shared contract format

Contract schema version `0.1` is the single semantic specification consumed by
the executable Python checker and the Lean module generator.

The canonical Bell example is distributed at
`src/fqv/data/bell.contract.json`. The matching circuit IR is
`examples/bell_ir.json`.

## Exact amplitudes

States use symbolic tokens instead of decimal approximations:

- `zero`
- `one` and `minus_one`
- `i` and `minus_i`
- `inv_sqrt_two` and `minus_inv_sqrt_two`

Python interprets these tokens as complex numbers for simulation. Lean maps
the same tokens to exact expressions such as `invSqrtTwo`. This decision
prevents a decimal approximation from becoming the statement of a formal
theorem.

Each state must contain exactly `2 ^ qubits` amplitudes. Version `0.1` does not
yet provide a general expression language for arbitrary algebraic amplitudes.

## Contract sections

- `initial_state` is the executable precondition.
- `target_state` is the exact state-preparation postcondition.
- `fidelity_threshold` controls the executable ideal-state comparison.
- `probabilities` define computational-basis observations.
- `resources` describe gate inventory constraints on the logical circuit.

Resource constraints are not part of the generated Lean state-correctness
theorem. They remain executable structural checks because transpilation may
change them without changing circuit semantics.

## Generating Lean

From an installed development environment:

```powershell
fqv-generate-lean `
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
fqv-generate-lean `
  examples/ghz3_ir.json `
  src/fqv/data/ghz3.contract.json `
  lean/QuantumValidation/GeneratedGhz3.lean
```

The generated proof enumerates computational-basis assignments. This is clear
and effective for small review cases, but its size grows exponentially with
the number of qubits. Larger parametric proofs will require reusable lemmas
instead of enumeration.

Generated modules should be reviewed as derived evidence. Editing them by hand
would break traceability to the source IR and contract.
