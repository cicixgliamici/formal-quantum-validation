# Coq and SQIR semantics

The Coq backend provides an independent formal path from the shared circuit IR
and contract format to SQIR and QuantumLib. It complements the native Lean
semantics; neither backend is treated as an oracle for the other.

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

## Validation strategy

The Coq CI job provides complementary evidence:

- byte-for-byte drift checks tie committed modules to JSON inputs;
- Bell, GHZ(3), and both fixed DJ obligations must compile;
- normalized DJ targets with a changed relative phase must be rejected;
- 248 basis obligations compare all supported gates with independent exact bit
  rules on registers of one to three qubits;
- both DJ Qiskit builders pass directly through extraction and Coq generation
  before `coqc` checks the resulting theorem.
- an invalid repeated-operand CNOT is proved neither source-well-formed nor
  SQIR-well-typed.

These are finite regressions. They do not establish equivalence between Lean
and Coq for arbitrary circuits, nor do they verify Qiskit or the translators.

## Basis order

The shared IR uses Qiskit's little-endian amplitude index. QuantumLib tensors
qubit zero on the left, so amplitude-index bit `k` is serialized into ket slot
`k`. The asymmetric DJ targets make a reversal visible; Bell and GHZ alone
cannot detect it because their target states are reversal-invariant.
