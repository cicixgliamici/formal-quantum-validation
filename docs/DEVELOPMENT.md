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
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
```

On a POSIX shell:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
```

The direct Python dependencies are pinned in `pyproject.toml`. Changes to
those versions must be reviewed together with the generated IR and regression
tests because Qiskit behavior is part of the executable trust boundary.

## Lean environment

Elan reads `lean-toolchain` and installs the matching Lean release
automatically:

```powershell
lake update
lake exe cache get
lake build
```

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

1. Update one toolchain at a time.
2. Record the exact version in the corresponding version file.
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
