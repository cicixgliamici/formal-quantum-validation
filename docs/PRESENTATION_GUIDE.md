# Project presentation guide

This guide organizes the repository's results into a short, defensible project
presentation. Claims should always distinguish formal proof from executable or
regression evidence.

## One-sentence contribution

The project connects a restricted, validated Qiskit circuit representation to
executable contracts, transpilation-equivalence evidence, and independently
kernel-checked Lean and Coq/SQIR proof obligations.

## Recommended narrative

1. Quantum measurements expose probabilities but can hide relative phase and
   do not establish universal correctness.
2. A small versioned IR and an exact contract format make the intended circuit
   and result explicit.
3. Qiskit supplies executable state, probability, resource, and transpilation
   evidence.
4. A replayable certificate turns the recognized `H; H -> I` rewrite into
   all-input Lean equality and complete SQIR operator equality.
5. Lean checks a native finite semantics, fixed examples, a parametric GHZ
   theorem, and preservation of inner products and normalization.
6. Coq lowers the shared gate language to SQIR, proves well-formed compilation,
   and checks generated exact-state obligations with QuantumLib semantics.
7. CI binds inputs, generators, generated artifacts, proof assistants, negative
   mutations, and cross-system semantic regressions.

## End-to-end view

```text
Qiskit circuit <-> checked IR + exact contract
      |                         |
      |                         +-> executable Qiskit checks
      |                         +-> transpilation equivalence evidence
      |                         +-> Lean obligation -> Lean kernel
      +-> fresh IR              +-> Coq obligation -> SQIR -> Coq kernel
```

## Claims and evidence

| Claim | Evidence | Important limitation |
| --- | --- | --- |
| Fixed Bell, GHZ(3), and DJ circuits reach exact targets | Generated Lean and Coq theorems | Fixed circuits, not all algorithms of each family |
| GHZ preparation is correct for every positive size | Parametric Lean theorem | Uses the formal fan-out constructor |
| Supported Lean circuits preserve inner products and normalization | General Lean theorems | Applies to the formal gate language |
| Coq lowering preserves structural validity | Generated well-formedness proofs and `circuit_well_formed_compile_preservation` | Does not verify correspondence with Qiskit |
| Transpilation preserves the complete operator in tested runs | Qiskit process fidelity and phase-adjusted matrix error | Numerical evidence, not a proof of the transpiler |
| Adjacent `H; H` elimination preserves semantics | Generated Lean all-input equality and Coq/SQIR operator equality | Exact certificate for one rewrite rule, not arbitrary transpilation |
| Gate conventions agree across boundaries for tested cases | Lean Qiskit-derived and Coq independent-basis regressions | Finite coverage; Coq reaches three qubits for I/X/Z/CNOT and two for H/SWAP |
| Qiskit DJ reaches Coq end to end | Direct builder-to-extractor-to-generator-to-`coqc` tests | Two fixed DJ variants |

## Case studies

- Bell demonstrates why exact amplitude comparison detects relative phase that
  computational-basis probabilities miss.
- GHZ(3) exercises a larger generated obligation; GHZ(n) demonstrates induction
  beyond finite enumeration. The fixed example uses a three-qubit CNOT chain,
  while the parametric theorem uses a qubit-zero fan-out for every nonempty
  size; both prepare the same target from the all-zero state.
- Deutsch-Jozsa uses asymmetric states to test bit ordering and includes
  constant and balanced fixed oracles plus negative relative-phase mutations.

Do not claim a proof of Deutsch-Jozsa for every promised oracle. The repository
contains two fixed two-query-qubit instances.

## Trust boundary

Lean and Coq kernels check the stated formal theorems. The mathematical gate
models, Qiskit, Python, extraction, generation, toolchains, and correspondence
between external circuits and formal definitions remain trusted to the extent
described in `TRUST_BOUNDARY.md`. Tests reduce this risk but do not eliminate it.

## How to explain the contract

The JSON file is the specification, not the proof. `fqv-verify` supplies
numerical evidence that the Qiskit execution satisfies it for the declared
input and tolerances. A Lean or Coq kernel accepting the generated exact
equality supplies formal evidence for the state-correctness fragment.

In Hoare notation the current contract resembles
`{ state = psi } circuit { state = phi }`. Through Curry-Howard, the formal
postcondition becomes a proposition and its proof becomes a term checked by
the kernel. This is narrower than a full Quantum Hoare Logic: the project does
not yet use quantum predicates over density operators or provide rules for
measurement, branching, and loops. See the
[contract format](CONTRACT_FORMAT.md#specification-numerical-check-and-formal-contract)
for the precise distinction.

## Suggested live demonstration

From a prepared development environment:

```powershell
fqv-verify --ir examples/bell_ir.json --contract src/fqv/data/bell.contract.json
fqv-verify `
  --ir examples/duplicate_h_ir.json `
  --contract examples/duplicate_h.contract.json `
  --transpile `
  --optimization-level 1 `
  --transpilation-certificate build/duplicate_h_certificate.json `
  --transpilation-proof-output build/GeneratedDuplicateHTranspilation.lean
lake env lean build/GeneratedDuplicateHTranspilation.lean
```

On Linux or WSL with the pinned Coq environment:

```bash
opam exec -- python -m pytest coq_tests/test_coq_compilation.py -v
```

Show the depth reduction from two gates to zero, the self-contained JSON
certificate, and the generated theorem before compiling it. A deliberately
rejected mutation then makes the distinction between successful generation and
kernel acceptance visible.

## Questions to anticipate

- Why use two proof assistants? They provide independent semantic paths: a
  compact native Lean model and an established SQIR/QuantumLib Coq backend.
- What is SQIR? It is Coq's Small Quantum Intermediate Representation: a typed
  unitary circuit language with complete matrix semantics, used as the formal
  target of the Coq lowering.
- Is GHZ(3) just the `n = 3` parametric circuit? No. The generated regression
  uses a CNOT chain; the universal theorem uses fan-out and induction. Lean
  proves both routes reach the corresponding GHZ state.
- Is the translator verified? No. Validation, drift checks, cross-system tests,
  and negative tests provide evidence, but translator correctness remains open.
- Why exact amplitude tokens? They prevent decimal approximations from becoming
  formal theorem statements.
- Does passing sampled measurements prove the target state? No. Relative phase
  can differ while measurement probabilities in one basis remain identical.
- Does operator equivalence certify hardware execution? No. Current checks use
  ideal unitary semantics and defer noise and physical-layout policies.
- Is the JSON contract already a formal proof? No. It states the obligation;
  numerical execution tests it, while kernel acceptance proves the generated
  exact equality.
- Is this a complete Quantum Hoare Logic? No. It is a concrete pure-state
  pre/post fragment, with separate general theorems for selected properties.

## Honest limitations and next steps

- IR 0.1 excludes measurement, reset, parameters, classical control, layouts,
  and stored global phase.
- Generated fixed-size proofs enumerate basis assignments and therefore scale
  exponentially.
- A verified extractor/generator correspondence would connect each generated
  well-formed circuit back to its original Qiskit object.
- A future verified lowering or certificate checker could remove Python
  translation from more of the trusted computing base.
- Hardware routing and noise require explicit logical-subspace and observation
  policies before meaningful claims can be made.
