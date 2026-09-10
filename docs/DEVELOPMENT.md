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
```

On a POSIX shell:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -c constraints-python312.txt -e ".[dev]"
python -m pip check
python -m pytest
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

## Lean environment

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

## Version update policy

## Matrix property tests

The commented pytest classes in `tests/test_matrix_properties.py` check the
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
