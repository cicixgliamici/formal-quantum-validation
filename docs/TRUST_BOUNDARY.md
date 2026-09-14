# Trusted computing base

The project distinguishes machine-checked mathematics from executable
evidence. A successful command is not, by itself, a proof of every component
in the pipeline.

## Machine-checked Lean foundation

- States and circuits are defined for every finite qubit count.
- Gate operands are bounded, and CNOT/SWAP operands are proved distinct.
- Gate semantics use Qiskit's documented little-endian basis order, and
  circuits execute from left to right.
- Lean checks exact target equalities for Bell, GHZ(3), and both fixed DJ cases.
- An inductive theorem proves GHZ preparation for every positive register size.
- Every supported circuit preserves complex inner products, squared norm, and
  normalization.
- Project declarations contain no `sorry`, project axiom, or opaque shortcut.

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

The generation pipeline produces the formal circuit, input state, target state,
and theorem statement from versioned JSON. Lean still checks the resulting proof.
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

The contract document is a specification, not a certificate. The executable
checker supplies numerical evidence under its tolerances and trusted runtime.
Kernel acceptance supplies formal evidence only for the exact semantic
statement emitted into Lean or Coq. This distinction follows the
Curry-Howard view of a checked proof term inhabiting the proposition, while the
contract's pre/post structure is a concrete pure-state analogue of a Hoare
triple. The project does not currently implement a general quantum-predicate
Hoare logic over density operators.

## Coq/SQIR regression

Generated clients use `QuantumValidation.Circuit`: public gate constructors,
ordered composition, SQIR lowering, and a shared proof tactic. The constructors
store natural-number operands without embedded proofs. Coq nevertheless defines
source-level well-formedness and proves that `compile_circuit` maps every
well-formed circuit to an SQIR `uc_well_typed` program. Generated clients prove
their source circuit well formed and derive this SQIR judgment automatically.
Checked IR and the Python translator nevertheless remain part of the end-to-end
trust boundary because Coq checks the generated circuit, not its correspondence
with the original Qiskit object.
The Coq gate regression checks 176 basis cases against independent exact bit
rules. I, X, Z, and CNOT reach three qubits; H and SWAP reach two due to the
pinned matrix tactic's dimension-eight timeout. Reversed operands,
non-adjacent operands, and spectator qubits are covered where applicable. It
also checks 14 empty-circuit cases and 3 complex-input cases. These finite caps
belong to regression execution, not to the formal `Gate dim` definition.

The separate Coq job compiles Bell, GHZ(3), and both fixed two-bit DJ examples
against the compiler and semantic libraries pinned in `coq/toolchain.env`.
Both DJ negative tests preserve normalization while changing a relative phase.
They first compile the correct theorem and the mutated definitions, then require
the mutated theorem to fail. Drift tests compare every generated `.v` artifact
with fresh production-generator output byte for byte.

A direct integration path constructs both DJ variants in Qiskit, extracts fresh
IR with the production frontend, generates Coq source, and requires `coqc` to
accept it. This connects the live Qiskit representation to Coq in one test, but
remains finite evidence rather than a proof that extraction or generation is
correct for arbitrary circuits.

These checks add Coq's kernel, SQIR/QuantumLib definitions and their imported
assumptions, and the Python Coq translator to the relevant trust boundary.
They do not prove the translator correct or establish equivalence of the two
formal backends for arbitrary circuits.

## Transpilation equivalence

The transpilation pipeline checks source and transpiled circuits with Qiskit's
complete operator representation, accounting for stored layout information and
global phase. This is stronger than comparing their behavior on the contract's
one initial state.

Qiskit, NumPy, the selected transpiler passes, and the numerical equivalence
threshold remain trusted. The numerical report alone is not a Lean or Coq
certificate that Qiskit's transpiler preserves semantics.

The separate exact-rewrite certificate narrows this limitation for
circuits reduced solely by adjacent `H; H` cancellation. A backend-neutral JSON
certificate embeds both checked IR endpoints and the rewrite positions. Lean
checks equality for every input state; Coq checks equality of complete SQIR
operators. The recognizer and generators remain untrusted proposers because a
forged or mistranslated obligation must still be rejected by the proof kernel.

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
