# Transpilation validation

The transpilation pipeline checks whether Qiskit transpilation preserves the
complete unitary transformation of a logical circuit. This is separate from
checking one state-preparation contract.

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
Export additionally requires zero stored global phase and no attached layout.
A phase-insensitive equivalence PASS does not waive these exact IR restrictions.
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
is not by itself a proof that the transpiler is semantics-preserving.

## Exact rewrite certificate proof of concept

The optional certificate path connects one deliberately small Qiskit
optimization to both formal backends. It currently recognizes only removal of
adjacent Hadamard pairs on the same qubit. The source and candidate cross the
normal checked-IR boundary, and the resulting self-contained JSON records each
`cancel_h_h` step with its position and target.

```powershell
fqv-verify `
  --ir examples/duplicate_h_ir.json `
  --contract examples/duplicate_h.contract.json `
  --transpile `
  --optimization-level 1 `
  --transpilation-certificate build/duplicate_h_certificate.json `
  --transpilation-proof-output build/GeneratedDuplicateHTranspilation.lean
```

The Lean generator emits a `CircuitEquivalent` theorem, which quantifies over
every input state. Select `--transpilation-proof-backend coq` and a `.v` output
to generate the analogous exact equality between complete SQIR operators.
Generation is not proof acceptance: run Lean or Coq on the emitted module.

Both formal generators deterministically replay the certificate before writing
an obligation. An unknown optimization or a mutated step fails closed. This is
intentionally a proof of one recognized rewrite trace, not a claim that all
Qiskit transpiler passes are verified.

Hardware routing is deferred. A physical backend may introduce extra ancilla
qubits, native parameterized gates, and non-trivial initial/final layouts.
Those cases need an explicit logical-subspace policy before they can be
reported without ambiguity.
