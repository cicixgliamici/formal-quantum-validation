# Architecture

The Python package is organized around dependency direction rather than around
the first Bell case study.

```text
domain        Qiskit-independent contracts, amplitudes, expectations, reports
ir            raw JSON boundary, validation, checked IR, linear operation order
frontend      adapters for external circuit systems
  qiskit      circuit conversion, extraction, execution, reference fixtures
backend       proof and evidence producers
  lean        deterministic Lean source generation
  coq         deterministic Coq source generation through Circuit.v
pipeline      orchestration of verification and transformation stages
```

## Dependency rules

- `domain` must not import Qiskit, Lean tooling, JSON file handling, or CLI
  code.
- Raw JSON is untrusted. Later stages consume `CheckedCircuitIr` whenever they
  do not specifically need the original contract artifact.
- `frontend.qiskit` owns every direct Qiskit circuit dependency.
- `backend.lean` and `backend.coq` translate validated inputs into proof
  obligations without executing Qiskit or invoking proof compilers.
- `pipeline` composes stages and owns workflow policy.
- The top-level modules such as `fqv.contracts` and `fqv.transpilation` are
  compatibility wrappers. New code should import the layered packages.

## Main flows

Executable verification:

```text
raw IR -> checked IR -> Qiskit circuit
                         + parsed domain contract
                         -> verification report
                         -> optional transpilation equivalence report
```

Formal obligation generation:

```text
raw IR -> validation ----+
                         +-> Lean backend -> generated theorem -> Lean kernel
                         +-> Coq backend -> Circuit.v / SQIR -> Coq kernel
raw contract -> parser --+
```

The command `fqv-verify` accepts arbitrary IR and contract paths. `fqv-bell`
remains an alias during the compatibility period.

## Coq abstraction boundary

`coq/QuantumValidation/Circuit.v` is the shared formal interface used by every
generated Coq module. It defines dimension-indexed `Gate` constructors for
`I`, `X`, `Z`, `H`, `CNOT`, and `SWAP`, and `Circuit dim` as an ordered gate list.
`compile_gate` owns the SQIR encodings, including `Z` as `Rz PI` and SWAP as
three CNOTs. `compile_circuit` preserves execution order, and `run` gives the
SQIR matrix semantics. The shared `solve_circuit` tactic reduces these
definitions and proves the resulting exact matrix and scalar equalities.

The Python generator serializes gate constructors and exact input/target
states. It does not duplicate gate decomposition or proof tactics. Generated
clients import `QuantumValidation.Circuit`, state equality using `run`, and
invoke `solve_circuit`. The test harness builds `Circuit.v` first in a fresh
session directory, then compiles clients against that artifact; a stale local
`Circuit.vo` cannot hide an error.

Operand bounds, distinct control/target operands, and positive register sizes
remain checked-IR preconditions. Coq gate constructors carry natural-number
operands rather than proofs of these conditions. In particular, the empty
circuit lowers to SQIR's `SKIP` on qubit zero and is supported for positive
dimensions only. This layer does not establish translator correctness.

## Regression and artifact boundaries

The default Python suite includes Coq artifact drift checks. The Python CI job
also regenerates and compares all four Lean artifacts: Bell, GHZ(3), DJ constant,
and DJ balanced. Separate Lean and Coq jobs compile the formal developments.

`coq_tests/test_gate_semantics.py` generates 248 gate/basis obligations covering
every valid placement of the six gates on one-, two-, and three-qubit registers.
Expected outputs come from independent bit rules and exact amplitude tokens,
not the SQIR compiler or production matrix code. Both operand orders,
non-adjacent operands, and spectator qubits are included. Additional cases check
empty circuits and signed/imaginary input serialization. The DJ tests require
both correct theorems to compile and both mutated targets to be rejected.

The existing Lean gate regression uses Qiskit-derived targets. The Coq basis
regression instead checks textbook gate action directly; neither finite suite
is a proof of cross-backend equivalence for arbitrary register sizes.

## Deutsch-Jozsa scope and basis order

The fixed DJ fixtures use query qubits 0 and 1 and ancilla qubit 2, with oracles
`f = 0` and `f(x0, x1) = x0`. Generated theorems prove exact target equality;
the additional Lean lemmas characterize those targets' query support. They do
not prove the algorithm for every promised oracle or establish query complexity.

The shared IR indexes amplitudes little-endian. QuantumLib tensors qubit zero
on the left, so the Coq serializer places bit `k` of the IR index in ket slot
`k`. Asymmetric DJ targets and gate/basis regressions exercise this conversion;
Bell and GHZ targets alone are invariant under qubit reversal.
