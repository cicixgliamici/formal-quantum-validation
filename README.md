# Formal Quantum Validation

Formal Quantum Validation combines executable Qiskit evidence with
kernel-checked Lean proofs for a restricted unitary circuit language.

Currently verified:

- Bell-state preparation;
- fixed GHZ(3) preparation;
- the full nonempty GHZ(n) family;
- unitarity and normalization preservation for every supported circuit.

The supported IR contains `I`, `X`, `Z`, `H`, `CNOT`, and `SWAP`.

Run executable verification for any checked IR and matching contract:

```powershell
fqv-verify `
  --ir examples/ghz3_ir.json `
  --contract src/fqv/data/ghz3.contract.json
```

Run all checks:

```powershell
python -m pytest
lake build
```

See [architecture](docs/ARCHITECTURE.md), the
[code study guide](docs/CODE_STUDY_GUIDE.md),
[development](docs/DEVELOPMENT.md), and the
[formal trust boundary](docs/TRUST_BOUNDARY.md).
