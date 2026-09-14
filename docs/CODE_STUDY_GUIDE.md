# Code study guide

This guide explains the repository in the order in which a reviewer should
study it. The central idea is that each layer adds meaning while keeping its
assumptions explicit.

## 1. Start from the shared artifacts

Read:

- `examples/bell_ir.json`;
- `src/fqv/data/bell.contract.json`;
- `docs/IR_CONVENTIONS.md`;
- `docs/CONTRACT_FORMAT.md`.

The IR describes what gates execute and in which order. The contract describes
what must be true about structure, input, output, and observable probabilities.
They are separate because one circuit may be checked against different
contracts, and one contract format may be consumed by different backends.

Questions to answer:

1. Why is qubit zero the least significant amplitude bit?
2. Which fields describe the circuit and which describe expected behavior?
3. Why are exact amplitudes symbolic strings instead of arbitrary JSON floats?

## 2. Follow raw data into the domain

Read:

- `src/fqv/domain/amplitudes.py`;
- `src/fqv/domain/expectations.py`;
- `src/fqv/domain/contracts.py`;
- `src/fqv/domain/contract_validation.py`;
- `src/fqv/domain/contract_parser.py`.

`QuantumContract` is intentionally boring: it is immutable data and has no
Qiskit, JSON, file, or Lean dependency. Parsing is separate so a malformed
document is not confused with a valid contract that a circuit fails to satisfy.

Study exercise:

1. Trace `"inv_sqrt_two"` from JSON to its Python complex value.
2. Find where a wrong state-vector dimension is rejected.
3. Explain why duplicate probability outcomes are ambiguous.

## 3. Study the IR trust boundary

Read:

- `src/fqv/ir/raw.py`;
- `src/fqv/ir/checked.py`;
- `src/fqv/ir/validation.py`;
- `src/fqv/ir/linear.py`;
- `src/fqv/ir/serialization.py`.

`RawCircuitIr` is only JSON-shaped data. `CheckedCircuitIr` is immutable and
can be created only after gate names, arities, indices, and distinct operands
have been checked. The current checked model is sequential and structural; it
is not yet the future resource-linear SSA model.

Study exercise:

1. Follow a raw CNOT through `_operation`.
2. List every invariant gained when `check_ir` succeeds.
3. Explain why operation order is stored in a tuple and never sorted.

## 4. Locate the Qiskit boundary

Read:

- `src/fqv/frontend/qiskit/extraction.py`;
- `src/fqv/frontend/qiskit/conversion.py`;
- `src/fqv/frontend/qiskit/circuits.py`.

Extraction maps provider objects to shared IR. Conversion maps checked IR back
to Qiskit. These functions are deliberately mechanical because a complicated
adapter is harder to trust. Measurements and parameters fail closed because IR
0.1 cannot represent their meaning.

Study exercise:

1. Verify the Qiskit-to-IR mapping of every supported gate.
2. Explain the barrier erase policy.
3. Identify why this frontend belongs to the bit-ordering trust boundary.

## 5. Understand executable verification

Read:

- `src/fqv/frontend/qiskit/checks/structure.py`;
- `src/fqv/frontend/qiskit/checks/state.py`;
- `src/fqv/frontend/qiskit/checks/probabilities.py`;
- `src/fqv/frontend/qiskit/verification.py`;
- `src/fqv/pipeline/verify.py`.

The checks are separate because they provide different evidence:

- structure catches resource and inventory mistakes;
- target-state comparison catches amplitude and relative-phase mistakes;
- exact probabilities check selected observables;
- sampled probabilities model finite-shot experiments.

The pipeline injects a verifier through a protocol. This keeps orchestration
independent from Qiskit even though the current executable frontend uses it.

Study exercise:

1. Explain why equal measurement probabilities do not imply equal states.
2. Find where global phase is accepted.
3. Explain why exact and sampled tolerances differ.

## 6. Understand transformation evidence and certification

Read:

- `src/fqv/pipeline/transpilation.py`;
- `src/fqv/pipeline/transpilation_certificate.py`;
- `src/fqv/domain/transpilation.py`;
- `src/fqv/backend/lean/transpilation.py`;
- `src/fqv/backend/coq/transpilation.py`;
- `lean/QuantumValidation/Transpilation.lean`.

The source and transpiled circuits are compared as complete operators, not only
on the contract input. One-input comparison would incorrectly accept distinct
operators that happen to agree on that input. The matrix error removes one
global phase but preserves every relative phase difference.

The exact certificate path is separate from that numerical report. It
recognizes a circuit change made solely of adjacent equal self-inverse gate
cancellations, records each `cancel_self_inverse` gate and its complete
operands, and deterministically replays the trace.
Lean then proves `CircuitEquivalent`, quantified over every input state. The
Coq backend proves equality of the complete SQIR operators. Any other rewrite,
or a trace that does not reconstruct the candidate IR, is rejected.

Study exercise:

1. Explain why the transpiler seed is part of the report.
2. Explain why process fidelity is paired with entry-wise error.
3. State clearly why this report is evidence rather than a Lean proof.
4. Trace `examples/duplicate_h_ir.json` through certificate recognition and
   deterministic replay.
5. Explain why certifying self-inverse cancellation does not certify arbitrary
   Qiskit passes.

## 7. Follow generation into the formal backends

Read:

- `src/fqv/backend/lean/generator.py`;
- `lean/QuantumValidation/GeneralCircuit.lean`;
- `lean/QuantumValidation/GeneralUnitarity.lean`;
- `lean/QuantumValidation/ParametricGhz.lean`.

The generator emits circuit data, state functions, and a theorem. Lean checks
the output, but Python generation remains in the trusted computing base.
Generated Bell and GHZ(3) proofs enumerate fixed bases; GHZ(n) uses a separate
inductive proof.

Before reading the long proofs, use the language summaries in
[general Lean semantics](GENERAL_SEMANTICS.md#lean-syntax-used-in-this-project)
and [Coq/SQIR semantics](COQ_SQIR.md#coq-syntax-used-in-this-project). They
explain the small set of declarations, types, and tactics needed to distinguish
definitions from propositions and proof automation from kernel acceptance.

Study exercise:

1. Trace one IR CNOT into its generated Lean constructor.
2. Explain why `(by decide)` is still useful after Python validation.
3. Distinguish generator correctness from kernel checking.
4. State the exact theorem proved for GHZ(n).
5. Compare the generated GHZ(3) CNOT chain with the parametric GHZ(n) fan-out
   and explain why their proofs use enumeration and induction respectively.

Then read:

- `src/fqv/backend/coq/generator.py`;
- `coq/QuantumValidation/Circuit.v`;
- `coq_tests/conftest.py`;
- `coq_tests/test_coq_compilation.py`;
- `coq_tests/test_gate_semantics.py`;
- `docs/COQ_SQIR.md`.

The Coq backend serializes the same checked IR and exact contract tokens into
a small public circuit language. `Circuit.v` lowers that language to SQIR and
uses QuantumLib matrix semantics. Its preservation theorem connects source
well-formedness to SQIR's `uc_well_typed`; this is distinct from proving that
the Python generator always emits the intended source circuit.

When explaining the implementation, assign one responsibility to each file:

- `generator.py` validates shared inputs and emits deterministic Coq source; it
  does not define gate matrices;
- `Circuit.v` defines the public gate language, lowers it to SQIR, proves typing
  preservation, and provides the proof tactics used by generated clients;
- `conftest.py` builds a fresh logical Coq library and invokes the pinned
  compiler, preventing stale `.vo` files from hiding failures;
- `test_coq_compilation.py` checks reviewed artifacts, the live Qiskit-to-Coq
  DJ route, deliberate target rejection, and invalid-operand rejection;
- `test_gate_semantics.py` supplies an independent bit-level oracle and checks
  generated gate obligations against the Coq kernel.

The production `solve_circuit` tactic and test-only `solve_basis_circuit` tactic
are intentionally separate. The latter handles concrete dimension-eight basis
terms aggressively; the former keeps false DJ mutations quick to reject. The
Coq regression covers 176 gate/basis obligations, 14 empty-circuit obligations,
and 3 signed or imaginary input cases. H and SWAP stop at two qubits because the
pinned tactic cannot reduce their dimension-eight terms within the CI timeout.

Study exercise:

1. Trace one Qiskit DJ circuit through extraction, generation, and `coqc`.
2. Explain why `circuit_well_formed` is separate from the `Gate` constructors.
3. State exactly what `circuit_well_formed_compile_preservation` proves.
4. Compare the independent Coq basis oracle with the Qiskit-derived Lean oracle.

## 8. Read the command last

Read `src/fqv/cli.py` only after understanding the layers. It contains very little
scientific logic: its job is to connect raw loading, checked construction,
frontend conversion, pipeline execution, and report I/O.

You should be able to explain the complete flow as:

```text
raw IR
  -> checked IR
  -> Qiskit circuit
  -> executable checks
  -> optional transpilation evidence

source IR + candidate IR
  -> recognized H;H rewrites
  -> replayable certificate
  +-> Lean all-input equivalence -> Lean kernel
  +-> Coq/SQIR operator equality -> Coq kernel

raw IR + raw contract
  +-> Lean generator -> generated theorem -> Lean kernel
  +-> Coq generator -> Circuit.v -> SQIR theorem -> Coq kernel
```

## 9. Presentation checklist

Before presenting, be able to answer:

1. What is formally proved and what is numerically checked?
2. Which components remain trusted?
3. Why is complete-operator equivalence stronger than state preparation?
4. Why does structural well-formedness not prove semantic correctness?
5. What guarantee could a future resource-linear IR add beyond IR 0.1?
6. What does the current Coq compilation-preservation theorem connect, and
   what translator-correctness result is still absent?
7. Why are Bell and fixed GHZ examples regressions rather than universal
   correctness claims?
8. Which part of the transpilation path is formally certified, and which part
   remains numerical evidence?
