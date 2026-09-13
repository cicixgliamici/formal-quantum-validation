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
- The top-level modules such as `fqv.contracts` and `fqv.transpilation` preserve
  the pre-refactor API throughout the 0.1 release line. New code should import
  the layered packages; removing wrappers requires an explicit versioned API
  decision rather than incidental cleanup.

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

Certified transpilation proof of concept:

```text
Qiskit source -> source IR -------+
Qiskit result -> candidate IR ----+-> exact rewrite certificate
                                      +-> Lean equivalence -> Lean kernel
                                      +-> Coq/SQIR equality -> Coq kernel
```

The certificate recognizer currently accepts only adjacent `H; H`
cancellations. Unsupported Qiskit optimizations fail closed instead of being
presented as formally certified.

The command `fqv-verify` accepts arbitrary IR and contract paths. `fqv-bell`
remains an alias throughout the 0.1 release line.

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

`solve_basis_circuit` is a test-only companion for concrete three-qubit basis
obligations. Keeping it separate matters: the production tactic must reject a
false DJ target promptly, while the basis tactic may use the more aggressive
dimension-eight matrix solver. Both still produce ordinary proof terms checked
by the Coq kernel.

Coq gate constructors carry natural-number operands rather than dependent
proofs. The separate `gate_well_formed` and `circuit_well_formed` predicates
state operand bounds, distinct binary operands, and positive register size.
`circuit_well_formed_compile_preservation` proves that compiling a well-formed
source circuit produces an SQIR `uc_well_typed` program. The positive-dimension
condition makes the empty circuit's `SKIP` on qubit zero well typed.

Checked IR enforces the same source conditions before generation. Generated
clients prove `circuit_well_formed` and derive SQIR `uc_well_typed` through the
preservation theorem before stating the semantic target equality. This still
does not verify the Python translator. See [Coq and SQIR semantics](COQ_SQIR.md)
for the exact boundary.

## Regression and artifact boundaries

The default Python suite includes Coq artifact drift checks. The Python CI job
also regenerates and compares all four Lean artifacts: Bell, GHZ(3), DJ constant,
and DJ balanced. Separate Lean and Coq jobs compile the formal developments.

`coq_tests/test_gate_semantics.py` generates 176 gate/basis obligations. I, X,
Z, and CNOT cover every valid placement through three qubits; H and SWAP cover
every placement through two because the pinned dimension-eight tactics exceed
the CI timeout for those gates.
Expected outputs come from independent bit rules and exact amplitude tokens,
not the SQIR compiler or production matrix code. Both operand orders,
non-adjacent operands, and spectator qubits are included where the configured
dimension permits. Cases are compiled in batches of eight to bound matrix-tactic
cost. Fourteen additional cases check empty circuits and three check
signed/imaginary input serialization. The DJ tests require
both correct theorems to compile and both mutated targets to be rejected.
They also build both DJ variants as live Qiskit circuits, extract fresh IR,
generate Coq obligations, and submit those obligations directly to `coqc`.

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
