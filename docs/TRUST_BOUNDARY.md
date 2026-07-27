# Trusted computing base

The project distinguishes machine-checked mathematics from executable
evidence. A successful command is not, by itself, a proof of every component
in the pipeline.

## Machine-checked in Milestone 2

- The two-qubit state space is represented by four complex amplitudes.
- Gate semantics use Qiskit's documented little-endian basis order.
- Circuits execute their gates from left to right.
- The Bell circuit is concrete formal data.
- Lean checks that the Bell circuit maps `|00>` to `|Phi+>`.
- The theorem contains no `sorry` and uses no Bell-specific axiom.

## Trusted components

- Lean's kernel and the definitions imported from mathlib
- The mathematical definitions in `QuantumValidation.Circuit`
- The Qiskit-to-IR extractor
- The future IR-to-Lean translator
- The claim that the chosen gate formulas model Qiskit correctly
- The Python interpreter, Qiskit implementation, operating system, and
  hardware used for executable experiments

## Current scope limitation

The primary formal semantics is now general in the finite qubit count. Gate
operands use `Fin n`, and CNOT/SWAP carry proofs that their operands differ.
The earlier two-qubit semantics remains only as an independent Bell regression
baseline.

Generated proofs currently enumerate basis assignments, so practical automatic
generation remains limited to small fixed-size circuits. Parametric circuit
families require reusable semantic lemmas and induction.

## Generated proof obligations

Milestone 3 generates the formal circuit, input state, target state, and
theorem statement from versioned JSON. Lean still checks the resulting proof.
CI regenerates the Bell module and rejects drift between source data and the
committed generated artifact.

The generator remains trusted to preserve the meaning of IR and contract
fields. Its validation and regression tests reduce this risk but do not turn
the Python generator itself into verified software.

## Transpilation equivalence

Milestone 4 checks source and transpiled circuits with Qiskit's complete
operator representation, accounting for stored layout information and global
phase. This is stronger than comparing their behavior on the contract's one
initial state.

Qiskit, NumPy, the selected transpiler passes, and the numerical equivalence
threshold remain trusted. Lean does not currently certify that Qiskit's
transpiler preserves semantics.

## Required validation

The next integration step must compare every formal gate against Qiskit's
statevector behavior on all computational-basis inputs. Those tests reduce the
risk of an ordering or operand-mapping error, but they do not remove the
extractor and semantic definitions from the trusted computing base.
