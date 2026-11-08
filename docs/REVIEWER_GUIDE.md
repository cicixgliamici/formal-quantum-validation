# Reviewer guide

This guide connects each project claim to the code and checks that support it.
Read the [README](../README.md) first for the problem, pipeline, and minimal demo.

## Short review

1. Read the evidence map below and the [trust boundary](TRUST_BOUNDARY.md).
2. Run the README's Bell and phase demos. The phase demo deliberately detects an
   error that computational-basis probabilities cannot distinguish.
3. Inspect the [CI runs](https://github.com/cicixgliamici/formal-quantum-validation/actions)
   for the commit being reviewed. Check all jobs, then open their test summaries
   and JUnit artifacts. A green Python job alone does not establish formal compilation.

## Claims and evidence

| Claim | Proof or implementation | Regression checks | Limit |
| --- | --- | --- | --- |
| Fixed circuits prepare the specified states | Lean [Bell](../lean/QuantumValidation/GeneratedBell.lean), [GHZ(3)](../lean/QuantumValidation/GeneratedGhz3.lean), [DJ constant](../lean/QuantumValidation/GeneratedDj2Constant.lean), [DJ balanced](../lean/QuantumValidation/GeneratedDj2Balanced.lean); matching [Coq clients](../coq/QuantumValidation) | [Coq compilation and mutations](../coq_tests/test_coq_compilation.py), [Coq drift](../tests/test_coq_drift.py), Lean compilation and drift in [CI](../.github/workflows/ci.yml) | Four fixed inputs and circuits; not all promised DJ oracles |
| GHZ preparation works for every positive size | [`ghz_correct`](../lean/QuantumValidation/ParametricGhz.lean) | [Python constructor regressions](../tests/test_validation_battery.py), [Lean regressions](../lean/QuantumValidation/RegressionTests.lean) | The parametric theorem uses fan-out; the fixed GHZ(3) example uses a chain |
| Supported Lean circuits preserve inner products, squared norm, and normalization | [`GeneralUnitarity.lean`](../lean/QuantumValidation/GeneralUnitarity.lean) | [Python matrix properties](../tests/test_matrix_properties.py), [Lean matrix checks](../lean/QuantumValidation/MatrixTests.lean) | Formal gate language; tests do not verify Qiskit itself |
| Coq lowering preserves well-formedness as SQIR typing | [`circuit_well_formed_compile_preservation`](../coq/QuantumValidation/Circuit.v) | [Generated clients and invalid operands](../coq_tests/test_coq_compilation.py) | Structural preservation, not correctness of Python extraction/generation |
| Equal adjacent self-inverse gates can be cancelled exactly | [Lean equivalence](../lean/QuantumValidation/Transpilation.lean), [Lean generator](../src/fqv/backend/lean/transpilation.py), [Coq generator](../src/fqv/backend/coq/transpilation.py) | [Python](../tests/test_transpilation_certificate.py), [Lean](../integration_tests/test_transpilation_certificate.py), [Coq](../coq_tests/test_transpilation_certificate.py) certificate tests | One rewrite class, not arbitrary transpiler passes |
| Tested gate conventions agree across boundaries | [Qiskit-to-Lean regression](../integration_tests/test_gate_semantics.py), [independent Coq basis oracle](../coq_tests/test_gate_semantics.py) | Lean: 248 gate/basis obligations; Coq: 176, plus 14 empty-circuit and 3 complex-input cases | Lean through three qubits; Coq H/SWAP through two, I/X/Z/CNOT through three |
| Numerical checks detect state and transpilation errors | [State checker](../src/fqv/frontend/qiskit/checks/state.py), [transpilation pipeline](../src/fqv/pipeline/transpilation.py) | [Matrix workflows](../tests/test_matrix_workflows.py), [transpilation tests](../tests/test_transpilation.py) | Numerical tolerances and trusted runtime; not kernel proofs |

The exact-state contract includes global phase. The numerical operator comparison
removes one global phase. A theorem proves the emitted formal statement; its
correspondence to the original Qiskit object still depends on trusted translation.

## Technical review

Follow the [architecture](ARCHITECTURE.md) for dependency direction, then the
[code study guide](CODE_STUDY_GUIDE.md) for the implementation reading order.
The [IR conventions](IR_CONVENTIONS.md) and [contract format](CONTRACT_FORMAT.md)
define the external inputs. The [Lean semantics](GENERAL_SEMANTICS.md),
[Coq/SQIR guide](COQ_SQIR.md), and
[transpilation guide](TRANSPILATION_VALIDATION.md) explain the formal boundaries.
Use [development](DEVELOPMENT.md) to reproduce each suite independently.

## Background documents

The [research project](RESEARCH_PROJECT.pdf)
and [introductory survey](QUANTUM_COMPUTING_SURVEY.pdf)
provide academic background. Use the current evidence map and source files above
to assess implemented results; the PDFs do not determine the current CI status.
