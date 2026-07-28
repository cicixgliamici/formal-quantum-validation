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

- `domain/amplitudes.py`;
- `domain/expectations.py`;
- `domain/contracts.py`;
- `domain/contract_validation.py`;
- `domain/contract_parser.py`.

`QuantumContract` is intentionally boring: it is immutable data and has no
Qiskit, JSON, file, or Lean dependency. Parsing is separate so a malformed
document is not confused with a valid contract that a circuit fails to satisfy.

Study exercise:

1. Trace `"inv_sqrt_two"` from JSON to its Python complex value.
2. Find where a wrong state-vector dimension is rejected.
3. Explain why duplicate probability outcomes are ambiguous.

## 3. Study the IR trust boundary

Read:

- `ir/raw.py`;
- `ir/checked.py`;
- `ir/validation.py`;
- `ir/linear.py`;
- `ir/serialization.py`.

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

- `frontend/qiskit/extraction.py`;
- `frontend/qiskit/conversion.py`;
- `frontend/qiskit/circuits.py`.

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

- `frontend/qiskit/checks/structure.py`;
- `frontend/qiskit/checks/state.py`;
- `frontend/qiskit/checks/probabilities.py`;
- `frontend/qiskit/verification.py`;
- `pipeline/verify.py`.

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

## 6. Understand transformation evidence

Read `pipeline/transpilation.py`.

The source and transpiled circuits are compared as complete operators, not only
on the contract input. One-input comparison would incorrectly accept distinct
operators that happen to agree on that input. The matrix error removes one
global phase but preserves every relative phase difference.

Study exercise:

1. Explain why the transpiler seed is part of the report.
2. Explain why process fidelity is paired with entry-wise error.
3. State clearly why this report is evidence rather than a Lean proof.

## 7. Follow generation into Lean

Read:

- `backend/lean/generator.py`;
- `lean/QuantumValidation/GeneralCircuit.lean`;
- `lean/QuantumValidation/GeneralUnitarity.lean`;
- `lean/QuantumValidation/ParametricGhz.lean`.

The generator emits circuit data, state functions, and a theorem. Lean checks
the output, but Python generation remains in the trusted computing base.
Generated Bell and GHZ(3) proofs enumerate fixed bases; GHZ(n) uses a separate
inductive proof.

Study exercise:

1. Trace one IR CNOT into its generated Lean constructor.
2. Explain why `(by decide)` is still useful after Python validation.
3. Distinguish generator correctness from kernel checking.
4. State the exact theorem proved for GHZ(n).

## 8. Read the command last

Read `cli.py` only after understanding the layers. It contains very little
scientific logic: its job is to connect raw loading, checked construction,
frontend conversion, pipeline execution, and report I/O.

You should be able to explain the complete flow as:

```text
raw IR
  -> checked IR
  -> Qiskit circuit
  -> executable checks
  -> optional transpilation evidence

raw IR + raw contract
  -> Lean generator
  -> generated theorem
  -> Lean kernel
```

## 9. Presentation checklist

Before presenting, be able to answer:

1. What is formally proved and what is numerically checked?
2. Which components remain trusted?
3. Why is complete-operator equivalence stronger than state preparation?
4. Why does linear ownership not prove safe ancilla release?
5. What new guarantee will the planned Linear IR add?
6. What would the proposed lowering-soundness theorem connect?
7. Why are Bell and GHZ regressions rather than the scientific novelty?
