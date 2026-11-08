# Formal Quantum Validation

[![CI](https://github.com/cicixgliamici/formal-quantum-validation/actions/workflows/ci.yml/badge.svg)](https://github.com/cicixgliamici/formal-quantum-validation/actions/workflows/ci.yml)

Formal Quantum Validation connects executable Qiskit checks with exact proofs
checked by Lean and Coq/SQIR for a restricted unitary circuit language.
Measurement probabilities can hide relative-phase errors; this project makes
the intended input and output states explicit and checks them across these layers.

The contribution is a shared, validated circuit IR and contract format, deterministic
proof generation, a parametric Lean development, and an exact certificate path
for one class of transpilation rewrites.

## How it works

```text
Qiskit circuit <-> checked IR + exact contract
                       |
                       +-> Qiskit execution -> numerical evidence
                       +-> Lean generation -> Lean kernel checks the theorem
                       +-> Coq generation -> SQIR -> Coq kernel checks the theorem

source IR + candidate IR -> replayable cancellation certificate
                       +-> Lean all-input equality / Coq operator equality
```

The supported gates are `I`, `X`, `Z`, `H`, `CNOT`, and `SWAP`.
The IR models unitary circuits; measurements and parameterized gates are outside
its current scope. Extraction and generation remain part of the
[trust boundary](docs/TRUST_BOUNDARY.md).

## Start here as a reviewer

- **Short review:** read the [claims and evidence](docs/REVIEWER_GUIDE.md), run
  the demo below, then read the [trust boundary](docs/TRUST_BOUNDARY.md).
- **Technical review:** follow the [architecture](docs/ARCHITECTURE.md) and
  [code study guide](docs/CODE_STUDY_GUIDE.md), then reproduce the checks in
  [development](docs/DEVELOPMENT.md).
- **Presentation:** use the [presentation guide](docs/PRESENTATION_GUIDE.md)
  and [live command guide](docs/SHOWOFF_GUIDE.md).

## Minimal executable demo

From the repository root, create a Python 3.12.10 environment and install the
pinned dependencies. On PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c constraints-python312.txt -e ".[dev]"
.\.venv\Scripts\fqv-verify.exe --ir examples/bell_ir.json --contract src/fqv/data/bell.contract.json
.\.venv\Scripts\fqv-demo-phase.exe
```

The Bell verification should pass. The phase demo should also exit successfully:
it demonstrates that a deliberately wrong relative phase passes the probability
checks but fails the exact-state contract. See the
[expected output](docs/PHASE_DEMO.md). These commands provide executable evidence;
formal compilation requires the separately installed Lean or Coq toolchain.
For POSIX setup, see [development](docs/DEVELOPMENT.md#python-environment).

## Results and limits

| Result | Evidence | Scope |
| --- | --- | --- |
| Bell, GHZ(3), and two Deutsch-Jozsa targets | Generated Lean and Coq proofs | Four fixed circuits; DJ uses `f = 0` and `f(x0, x1) = x0` |
| GHZ preparation for every positive register size | Inductive Lean proof | Formal fan-out circuit family |
| Unitarity and normalization preservation | General Lean proofs | Every circuit in the supported formal language |
| Well-formed Coq circuits compile to well-typed SQIR | Coq preservation theorem | Structural validity, not Python translator correctness |
| Adjacent equal self-inverse gates cancel | Exact Lean and Coq certificates | `X`, `Z`, `H`, `CNOT`, `SWAP`; one rewrite class |

The [evidence map](docs/REVIEWER_GUIDE.md#claims-and-evidence) links each result
to its source and regression checks. Numerical transpilation equivalence is
phase-insensitive; state contracts and formal target equalities include global
phase. No general correctness theorem for Qiskit's transpiler, the Python
translators, or all Deutsch-Jozsa oracles is claimed.

## Repository map

| Location | Responsibility |
| --- | --- |
| `src/fqv/domain`, `src/fqv/ir` | Contracts, exact amplitude tokens, checked circuit representation |
| `src/fqv/frontend/qiskit` | Extraction, execution, numerical checks |
| `src/fqv/backend`, `src/fqv/pipeline` | Proof generation and workflow orchestration |
| `lean`, `coq` | Formal semantics, reusable proofs, generated clients |
| `examples`, `schemas` | Reviewable circuit inputs and interchange formats |
| `tests` | Python regressions, generated-source drift, documentation, formal source policy |
| `integration_tests`, `coq_tests` | Tests requiring Lean or Coq/SQIR |
| `docs` | Review, design, setup, and presentation guides |

Generated demonstration output belongs in ignored `build/`. Top-level Python
compatibility wrappers are explained in the [architecture](docs/ARCHITECTURE.md).

## Continuous integration

The [CI workflow](.github/workflows/ci.yml) runs on pushes and pull requests:

| Job | Checks |
| --- | --- |
| Python on Linux and Windows | Ruff, executable tests, dependency compatibility, installed CLI, Lean/Coq source drift, Lean source policy |
| Lean | Formal development build, Qiskit-to-Lean semantic regressions, exact rewrite certificates |
| Coq | Pinned Coq/SQIR setup, source drift, formal examples, gate semantics, rejected mutations, exact rewrite certificates |

Each job publishes a test summary and downloadable JUnit reports when available.
The source policy rejects Lean proof placeholders and project `axiom`/`opaque`
tokens; it is a syntactic guard, not an audit of imported assumptions.

After the [toolchain setup](docs/DEVELOPMENT.md), reproduce the checks with:

```text
python -m ruff check src tests coq_tests integration_tests scripts
python -m pytest
python -m pip check
lake build
python -m pytest integration_tests -v
opam exec -- python -m pytest coq_tests -v
```

The final command requires Linux or WSL and the pinned opam environment.
