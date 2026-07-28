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
pipeline      orchestration of verification and transformation stages
```

## Dependency rules

- `domain` must not import Qiskit, Lean tooling, JSON file handling, or CLI
  code.
- Raw JSON is untrusted. Later stages consume `CheckedCircuitIr` whenever they
  do not specifically need the original contract artifact.
- `frontend.qiskit` owns every direct Qiskit circuit dependency.
- `backend.lean` translates validated inputs into proof obligations but does
  not execute Qiskit.
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
raw contract -> parser --+
```

The command `fqv-verify` accepts arbitrary IR and contract paths. `fqv-bell`
remains an alias during the compatibility period.
