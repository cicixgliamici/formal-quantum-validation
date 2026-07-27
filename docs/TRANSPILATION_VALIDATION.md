# Transpilation validation

Milestone 4 checks whether Qiskit transpilation preserves the complete unitary
transformation of a logical circuit. This is separate from checking one
state-preparation contract.

For example, identity and `Z` both preserve `|0>`, but they are not equivalent
operators because they act differently on superpositions. The transpilation
check therefore compares operators rather than only the Bell input state.

## Reproducible configuration

The pipeline records:

- Qiskit optimization level
- transpiler random seed
- requested basis gates
- source and transpiled depths
- source and transpiled gate counts
- whether Qiskit attached a layout

The default gate basis matches IR version `0.1`. This allows a successful
logical transpilation to continue through the existing IR-to-Lean pipeline.
Hardware-native bases containing parameterized rotations are not yet accepted
by the formal IR.

Qiskit's preset transpiler contains stochastic and heuristic passes. A fixed
`seed_transpiler` makes repeated runs reproducible for identical inputs and
tool versions. Qiskit versions remain pinned because pass implementations may
change between releases.

## Equivalence criterion

The checker constructs the complete `Operator` for both circuits using
`Operator.from_circuit`. This method applies layout information stored on a
transpiled circuit when mapping it back to the abstract qubit space.

Two checks must pass:

1. Process fidelity meets the configured threshold.
2. Matrix entries agree after removing one global phase.

Process fidelity is independent of global phase for unitary operators. The
second check supplies a directly interpretable maximum numerical error and
protects the report from relying on a single aggregate metric.

## Command

```powershell
fqv-bell `
  --transpile `
  --optimization-level 2 `
  --seed-transpiler 11 `
  --transpiled-ir-output build/bell_transpiled_ir.json `
  --equivalence-report build/bell_equivalence.json
```

The command fails if either the original executable contract or transpilation
equivalence fails.

## Scope and trust boundary

This milestone uses ideal unitary semantics. It rejects circuits containing
measurements or other operations that cannot be converted to `Operator`.

The result is executable equivalence evidence produced by Qiskit and NumPy; it
is not yet a Lean proof that the transpiler is semantics-preserving. A future
certificate-producing or verified transformation layer would be required for
that stronger claim.

Hardware routing is deferred. A physical backend may introduce extra ancilla
qubits, native parameterized gates, and non-trivial initial/final layouts.
Those cases need an explicit logical-subspace policy before they can be
reported without ambiguity.
