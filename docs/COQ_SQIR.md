# Coq and SQIR semantics

The Coq backend provides an independent formal path from the shared circuit IR
and contract format to SQIR and QuantumLib. It complements the native Lean
semantics; neither backend is treated as an oracle for the other.

## What SQIR provides

SQIR stands for **Small Quantum Intermediate Representation**. It is a
formally defined circuit language for Coq, designed to make quantum programs
small enough to reason about while retaining precise typing and mathematical
semantics. In this project SQIR is the central semantic target of the Coq
backend, not merely a serialization format.

The relevant SQIR concepts are:

- `base_ucom dim`, the type of unitary commands over a register of `dim`
  qubits;
- operations such as `H`, `X`, `Rz`, and `CNOT`, together with sequential
  composition `;`;
- `uc_well_typed`, the proposition that every referenced qubit is valid and
  multi-qubit operands satisfy SQIR's structural requirements;
- `uc_eval`, the denotational semantics that maps a unitary command to its
  complete `2^dim` by `2^dim` matrix;
- the QuantumLib matrix library and tactics used to reduce exact matrix
  equalities to scalar equalities.

The project first represents the shared IR with its own small `Gate` language,
then `compile_gate` and `compile_circuit` lower that language to `base_ucom`.
This separation exposes a reviewable compiler boundary. The preservation
theorem proves that a well-formed source circuit becomes a well-typed SQIR
program, while correctness obligations use `uc_eval` to state exact behavior.

SQIR is particularly valuable here because Coq checks both the structural
argument and the resulting matrix proof. The implementation therefore reuses
an established formal quantum IR instead of asking reviewers to trust a second
ad hoc Python matrix simulator.

## Coq syntax used in this project

A reviewer only needs a small part of the language to follow the development:

- `Inductive Gate ... := ...` declares an algebraic data type. Each constructor
  (`GateH`, `GateCNOT`, and so on) is one possible gate value.
- `Definition` introduces a named term without recursion. It defines
  `Circuit`, validity predicates, individual gate lowering, and `run`.
- `Fixpoint` defines structurally recursive functions. `compile_circuit`
  recursively lowers an ordered gate list and is accepted because each call
  consumes the remaining list.
- `match value with ... end` performs case analysis on a gate or list.
- `Prop` is the universe of propositions. `gate_well_formed` and
  `uc_well_typed` are properties to prove rather than Boolean runtime checks.
- `Lemma` and `Theorem` introduce proof obligations. `Proof. ... Qed.` encloses
  the tactic script and stores the kernel-checked result.
- `Ltac` defines proof automation. `solve_circuit` constructs proof terms by
  unfolding the lowering, evaluating SQIR matrices, and solving exact scalar
  equations; the tactic itself is not added as an axiom.
- Implicit parameters in braces, such as `{dim : nat}`, let Coq infer the
  register dimension from surrounding terms.

Common proof commands are also local and readable: `intros` introduces
hypotheses, `destruct` and `induction` split data into cases, `apply` uses a
known implication or theorem, `exact` supplies the required term, and `cbn`,
`simpl`, or `rewrite` reduce definitions and equalities. The final authority is
always the proof term checked at `Qed`, not the tactic transcript.

## Formal representation

`coq/QuantumValidation/Circuit.v` defines `Gate dim` with constructors for `I`,
`X`, `Z`, `H`, `CNOT`, and `SWAP`. A `Circuit dim` is an execution-ordered list.
Operands are natural numbers so generated files remain small and readable.

Source validity is stated separately:

- `gate_well_formed` requires every operand to be below `dim` and the two
  operands of CNOT or SWAP to differ;
- `circuit_well_formed` requires a positive dimension and every gate to be
  well formed.

The positive dimension covers the empty circuit because SQIR's `SKIP` is an
identity gate on qubit zero.

## Lowering and preservation

`compile_gate` translates public gates into `base_ucom dim`. Identity, X, H,
and CNOT use the corresponding SQIR operations. Z is represented by `Rz PI`,
and SWAP is decomposed into three CNOTs. `compile_circuit` preserves list order,
while `run` applies SQIR's `uc_eval` matrix semantics.

Two checked results connect the layers:

```coq
compile_gate_well_typed :
  gate_well_formed gate -> uc_well_typed (compile_gate gate)

circuit_well_formed_compile_preservation :
  circuit_well_formed circuit ->
  uc_well_typed (compile_circuit circuit)
```

The second theorem proves that lowering preserves structural validity for every
source circuit. It does not prove the Python extractor or generator correct.
Generated modules also prove their concrete circuit well formed and derive
`uc_well_typed` through the preservation theorem.

## Generated correctness obligations

The Python backend emits definitions for the circuit, exact input vector, and
exact target vector. The generated theorem has the form:

```coq
run generated_circuit × generated_input = generated_target
```

`solve_circuit` unfolds the compiler, evaluates SQIR matrices, and discharges
the resulting exact scalar equalities. Coq's kernel checks the final proof term.
Resource limits and sampled probabilities remain executable contract checks and
are not part of this theorem.

There are two proof tactics because they serve different jobs:

- `solve_circuit` is the production tactic emitted into generated Bell, GHZ,
  and DJ clients. It keeps symbolic reduction predictable, including when a
  deliberately false mutation must be rejected quickly;
- `solve_basis_circuit` is used only by concrete three-qubit basis regressions.
  It unfolds composite identities and invokes QuantumLib's optimized matrix
  solver for dimension-eight terms.

Both tactics rewrite `phase_shift PI` with `phase_pi`. SQIR lowers public Z to
`Rz PI`, whose evaluated matrix is otherwise left in phase-shift form by the
generic simplifier.

## Certified self-inverse cancellation

The Coq transpilation backend consumes the backend-neutral exact-rewrite
certificate. Before generating Coq, Python deterministically replays every
`cancel_self_inverse` step and requires the reconstructed circuit to match the checked
candidate IR. The emitted theorem compares complete SQIR operators:

```coq
run duplicate_h_transpilation_source =
  run duplicate_h_transpilation_candidate
```

`solve_circuit` proves the equality by reducing the duplicated `X`, `Z`, `H`,
`CNOT`, or `SWAP` applications.
This result covers every input state because it is an operator equality. It
certifies the recorded cancellation trace only; it does not verify Qiskit's
general optimization pipeline or the Python recognizer.

## Validation strategy

The Coq CI job provides complementary evidence:

- byte-for-byte drift checks tie committed modules to JSON inputs;
- Bell, GHZ(3), and both fixed DJ obligations must compile;
- normalized DJ targets with a changed relative phase must be rejected;
- 176 gate/basis obligations compare all supported gates with independent exact
  bit rules. I, X, Z, and CNOT reach three qubits; H and SWAP reach two;
- 14 empty-circuit obligations check identity behavior, and 3 additional cases
  exercise negative and imaginary amplitude serialization;
- both DJ Qiskit builders pass directly through extraction and Coq generation
  before `coqc` checks the resulting theorem;
- the generated adjacent self-inverse operator equality must compile, while a mutated
  certificate must be rejected before generation;
- an invalid repeated-operand CNOT is proved neither source-well-formed nor
  SQIR-well-typed.

These are finite regressions. They do not establish equivalence between Lean
and Coq for arbitrary circuits, nor do they verify Qiskit or the translators.
The H/SWAP dimension cap is a test-runner constraint, not a restriction of the
IR or `Gate dim`: with the pinned QuantumLib version, those dimension-eight
proof terms do not reduce reliably within the 600-second per-module timeout.

### How the gate regression works

`coq_tests/test_gate_semantics.py` deliberately avoids the production matrix
implementation when computing expected states. Python bit operations implement
the textbook action of each gate on a basis index. The test then serializes that
independently computed vector through the production Coq generator and asks
`coqc` to prove the equality.

Generated cases are grouped into modules of at most eight obligations. Modules
avoid theorem-name collisions, while bounded batches prevent Coq tactic cost
from growing nonlinearly and make the 600-second timeout meaningful. A failure
therefore identifies a concrete gate, register size, placement, and basis input.

## Basis order

The shared IR uses Qiskit's little-endian amplitude index. QuantumLib tensors
qubit zero on the left, so amplitude-index bit `k` is serialized into ket slot
`k`. The asymmetric DJ targets make a reversal visible; Bell and GHZ alone
cannot detect it because their target states are reversal-invariant.
