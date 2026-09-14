# Development instructions

The project uses pinned Python and Lean toolchains so that executable checks
and formal proofs can be reproduced in local environments and CI.

## Prerequisites

- Python 3.12.10
- `venv` and `pip`
- Elan, the Lean toolchain manager
- Git

Python 3.14 is intentionally not used as the project baseline. The supported
version is recorded in `.python-version` and enforced by `pyproject.toml`.

## Python environment

Create and activate an isolated environment from the repository root.

On PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -c constraints-python312.txt -e ".[dev]"
python -m pip check
python -m pytest
python -m ruff check src tests coq_tests integration_tests
```

On a POSIX shell:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -c constraints-python312.txt -e ".[dev]"
python -m pip check
python -m pytest
python -m ruff check src tests coq_tests integration_tests
```

The direct Python dependencies are pinned in `pyproject.toml`; the tested
transitive versions are pinned in `constraints-python312.txt`. Use that file
for development and CI installs rather than resolving new versions each time.
Changes to
those versions must be reviewed together with the generated IR and regression
tests because Qiskit behavior is part of the executable trust boundary.

On Windows, commands can also be run explicitly through
`.\.venv\Scripts\python.exe` without activating PowerShell scripts. A global
Python 3.14 installation is not a substitute for this Python 3.12 environment.
The default `fqv-verify` example uses packaged resources and works outside the
repository; custom `--ir` and `--contract` paths remain relative to the caller.

Ruff checks correctness errors, import ordering, and core Python style in CI.
`tests/test_documentation.py` verifies every local Markdown link without making
documentation tests depend on external network availability.

## Coq environment

Use Linux or WSL with opam installed. `coq/toolchain.env` pins OCaml 4.14.1,
Coq 8.19.2, QuantumLib 1.7.0, and an exact SQIR Git commit. The setup script
builds only upstream `SQIR.v` and `UnitarySem.v`, the complete SQIR dependency
closure used here; VOQC and upstream examples are not required.

```bash
source coq/toolchain.env
opam switch create fqv-coq "$OCAML_VERSION"
eval "$(opam env --switch=fqv-coq)"
bash coq/setup.sh
python -m pytest tests/test_coq_drift.py -v
opam exec -- python -m pytest coq_tests -v
```

Install the Python project in a Python 3.12 environment as described above.
The Coq suite first compiles the shared `Circuit.v` abstraction, then compiles
the four generated clients against it in temporary directories.
It also constructs both Deutsch-Jozsa variants in Qiskit, extracts fresh IR,
generates Coq source, and submits the resulting obligations to `coqc`. This is
the direct Qiskit-to-Coq integration path; it does not read committed DJ IR.
For both DJ examples it compiles a freshly generated correct target, checks
the mutated definitions separately, and requires compilation of the false
theorem to fail. Missing tools, imports, and timeouts fail the suite. The
separate CI Coq job runs the same commands; Lean integration tests remain
independent. The default Python suite checks byte-for-byte drift for all four
generated `.v` files and requires coverage of any newly added generated module.

The same Coq job runs `coq_tests/test_gate_semantics.py`: 176 obligations compare
all six gates with independent exact basis-action rules. I, X, Z, and CNOT are
checked through three qubits; H and SWAP are checked through two because their
dimension-eight proof terms exceed the pinned tactic's per-module timeout.
Another 14 obligations cover empty circuits and 3 cover signed/imaginary inputs.
Cases are compiled in batches of eight to bound tactic cost. To run only this
regression, use `opam exec -- python -m pytest coq_tests/test_gate_semantics.py -v`.

To update generated Coq source, use `python -m fqv.generate_cli --backend coq`
with the example IR, matching contract, and committed destination. Review
toolchain changes together with regenerated artifacts and rerun both suites.
The compiler and semantic libraries are pinned; opam's host/build dependencies
are resolved by opam, so this is not a bit-identical operating-system image.

## Lean environment

The Python CI job checks generated Lean source for drift on both Linux and
Windows. It regenerates Bell, GHZ(3), DJ constant, and DJ balanced into temporary
files and compares each with its committed `lean/QuantumValidation/Generated*.lean`
counterpart. Any difference fails CI; regeneration does not overwrite the
committed artifacts. The separate Lean job compiles the formal development.

To reproduce the DJ comparisons locally in PowerShell:

```powershell
python -m fqv.generate_cli examples/dj2_constant_ir.json src/fqv/data/dj2_constant.contract.json build/GeneratedDj2Constant.lean
python -m fqv.generate_cli examples/dj2_balanced_ir.json src/fqv/data/dj2_balanced.contract.json build/GeneratedDj2Balanced.lean
git diff --no-index --exit-code lean/QuantumValidation/GeneratedDj2Constant.lean build/GeneratedDj2Constant.lean
git diff --no-index --exit-code lean/QuantumValidation/GeneratedDj2Balanced.lean build/GeneratedDj2Balanced.lean
```

When intentionally changing an IR, contract, or generator, regenerate the
affected committed modules, review the diff, and run `lake build` before
submitting the change.

Elan reads `lean-toolchain` and installs the matching Lean release
automatically:

```powershell
lake update
lake exe cache get
lake build
```

After building Lean, run the cross-system integration suite:

```powershell
python -m pytest integration_tests -v
```

This compiles 248 Qiskit-derived gate/basis obligations in Lean and checks that
a deliberately false target is rejected. It covers all supported gate placements
on one-, two-, and three-qubit registers. The suite is separate from the default
Python tests because it requires both installed toolchains and built Lean imports;
CI runs it in the Lean job. A missing toolchain is a failure, not a skipped test.

Check deterministic transpilation and complete operator equivalence:

```powershell
fqv-verify `
  --ir examples/bell_ir.json `
  --contract src/fqv/data/bell.contract.json `
  --transpile `
  --optimization-level 2 `
  --seed-transpiler 11 `
  --equivalence-report build/bell_equivalence.json
```

`lakefile.toml` pins mathlib to the release matching Lean. Update Lean and
mathlib together; using mismatched releases is unsupported. The formal
development contains no project `sorry`, `axiom`, or `opaque` declaration.

### Exact self-inverse transpilation certificate

The formally certified path supports one rewrite class: cancellation of two
adjacent equal `X`, `Z`, `H`, `CNOT`, or `SWAP` gates. Generate the checked
endpoints, replayable certificate, and Lean obligation with:

```powershell
fqv-verify `
  --ir examples/duplicate_h_ir.json `
  --contract examples/duplicate_h.contract.json `
  --transpile `
  --optimization-level 1 `
  --seed-transpiler 7 `
  --transpiled-ir-output build/duplicate_h_transpiled.json `
  --equivalence-report build/duplicate_h_equivalence.json `
  --transpilation-certificate build/duplicate_h_certificate.json `
  --transpilation-proof-output build/GeneratedDuplicateHTranspilation.lean

lake env lean build/GeneratedDuplicateHTranspilation.lean
```

Use `--transpilation-proof-backend coq` with a `.v` output to produce the SQIR
operator-equality obligation. Both generators replay the certificate before
writing. Unsupported optimizations and mutated traces fail closed. The Python,
Lean, and Coq vertical slices are covered independently:

```powershell
python -m pytest tests/test_transpilation_certificate.py -v
python -m pytest integration_tests/test_transpilation_certificate.py -v
```

```bash
opam exec -- python -m pytest coq_tests/test_transpilation_certificate.py -v
```

These checks certify recorded self-inverse cancellations, not arbitrary
transpilation.
Generated demonstration artifacts belong in `build/` and are not committed.

## Running the prototype

After installing the Python project:

```powershell
fqv-verify `
  --ir examples/bell_ir.json `
  --contract src/fqv/data/bell.contract.json `
  --ir-output build/bell_ir.json `
  --json-report build/bell_report.json
```

Generated verification artifacts belong in `build/` and are not committed.

Generate and check the Lean obligation derived from the shared Bell contract:

```powershell
fqv-generate-lean `
  examples/bell_ir.json `
  src/fqv/data/bell.contract.json `
  lean/QuantumValidation/GeneratedBell.lean
lake build
```

## Matrix property tests

The pytest classes in `tests/test_matrix_properties.py` check the
actual IR-to-Qiskit matrices against independent literal matrices. They test
both adjoint identities, self-inversion of the supported gates, and preservation
of norms and complex inner products. Negative examples include a projector,
scaled identity, unnormalized Hadamard, and a matrix with identical unit columns.

`tests/test_matrix_workflows.py` follows matrix behavior through contract reports,
all four transpilation optimization levels, and the CLI's files and exit codes.
Its mutated circuits remain unitary but fail the intended state contract.

```powershell
python -m pytest tests/test_matrix_properties.py tests/test_matrix_workflows.py -v
lake build QuantumValidation.MatrixTests
```

`lean/QuantumValidation/MatrixTests.lean` groups exact theorem-based tests into
namespaces. It checks concrete complex matrices and proves counterexamples,
then connects the X, Z, and H matrix actions to the existing gate semantics.
The Hadamard bridge also transfers norm and inner-product preservation for
arbitrary complex input vectors. `lake build` includes this module automatically.
The diagnostic phase matrix is not an extension of the supported IR gate set.

## Version update policy

1. Update one toolchain at a time.
2. Record the exact version in the corresponding version file.
   For Python dependencies, update the tested transitive constraints as well.
3. Run both `python -m pytest` and `lake build`.
4. Inspect the exported Bell IR for semantic changes.
5. Commit version changes and compatibility fixes together.

Local planning is maintained in `ROADMAP.local.md`. The file is intentionally
excluded from Git so that exploratory notes do not become project evidence.

## Python architecture

New code should follow the dependency boundaries documented in
`docs/ARCHITECTURE.md`. In particular, domain and checked IR modules remain
independent from Qiskit. Top-level modules retained from the MVP are
compatibility wrappers and should not receive new business logic.
