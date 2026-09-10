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
- The IR-to-Lean translator
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
On both Linux and Windows, the Python CI job regenerates the Bell, GHZ(3),
DJ constant, and DJ balanced Lean modules from their committed IR and contracts.
It compares temporary output with all four committed `.lean` artifacts and
rejects any drift. Compilation remains a separate check in the Lean job.

Generated equality includes global phase. The executable state contract uses
the same convention with a numerical roundoff tolerance; the separate operator
equivalence report remains explicitly phase-insensitive. Neither report proves
the Python translator correct.

The generator remains trusted to preserve the meaning of IR and contract
fields. Its validation and regression tests reduce this risk but do not turn
the Python generator itself into verified software.

## Coq/SQIR regression

Generated clients use `QuantumValidation.Circuit`: public gate constructors,
ordered composition, SQIR lowering, and a shared proof tactic. Operand bounds
remain Python checked-IR preconditions, not proofs carried by Coq constructors.
The Coq gate regression checks 248 basis cases against independent exact bit
rules for all six gates on one to three qubits, including reversed and
non-adjacent operands. It also checks empty circuits and complex inputs.

The separate Coq job compiles Bell, GHZ(3), and both fixed two-bit DJ examples
against the compiler and semantic libraries pinned in `coq/toolchain.env`.
Both DJ negative tests preserve normalization while changing a relative phase.
They first compile the correct theorem and the mutated definitions, then require
the mutated theorem to fail. Drift tests compare every generated `.v` artifact
with fresh production-generator output byte for byte.

These checks add Coq's kernel, SQIR/QuantumLib definitions and their imported
assumptions, and the Python Coq translator to the relevant trust boundary.
They do not prove the translator correct or establish equivalence of the two
formal backends for arbitrary circuits.

## Transpilation equivalence

Milestone 4 checks source and transpiled circuits with Qiskit's complete
operator representation, accounting for stored layout information and global
phase. This is stronger than comparing their behavior on the contract's one
initial state.

Qiskit, NumPy, the selected transpiler passes, and the numerical equivalence
threshold remain trusted. Lean does not currently certify that Qiskit's
transpiler preserves semantics.

## Cross-system semantic regression

`integration_tests/test_gate_semantics.py` compares every supported gate with
Qiskit on every computational-basis input for registers of one, two, and three
qubits. It covers every valid operand placement, including reversed CNOT roles,
both SWAP orders, non-adjacent operands, and spectator qubits: 248 cases in all.

Qiskit computes the expected amplitudes. The production extractor and generator
translate each circuit and target, then `lake env lean` checks the resulting
theorems against the formal gate semantics. A normalized target with one
deliberately incorrect branch sign must be rejected by Lean. Missing tooling
or compiler errors fail the integration suite rather than silently skipping it.

This is a finite regression test across two systems, not a formal equivalence
proof for arbitrary register sizes or a verification of Qiskit, the extractor,
or the generator. These components remain in the trusted computing base.
