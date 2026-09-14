# Formal Quantum Validation

Formal Quantum Validation combines executable Qiskit evidence with
kernel-checked Lean and Coq/SQIR proofs for a restricted unitary circuit language.

Currently verified:

- Bell-state preparation;
- fixed GHZ(3) preparation;
- two fixed Deutsch-Jozsa examples: constant `f = 0` and balanced `f(x0, x1) = x0`;
- the full nonempty GHZ(n) family in Lean;
- unitarity and normalization preservation for every supported circuit in Lean;
- preservation from well-formed Coq circuits to SQIR `uc_well_typed` programs.
- exact Lean and Coq/SQIR certificates for adjacent equal self-inverse gate
  cancellation (`X`, `Z`, `H`, `CNOT`, and `SWAP`).

The supported IR contains `I`, `X`, `Z`, `H`, `CNOT`, and `SWAP`.

Run executable verification for any checked IR and matching contract:

```powershell
fqv-verify `
  --ir examples/ghz3_ir.json `
  --contract src/fqv/data/ghz3.contract.json
```

Run the default Python and Lean checks:

Use the Python 3.12.10 environment described in
[development](docs/DEVELOPMENT.md), with `constraints-python312.txt` applied.

```powershell
python -m pytest
python -m pip check
lake build
```

The toolchain-dependent integration suites run separately:

```powershell
python -m pytest integration_tests -v
```

```bash
opam exec -- python -m pytest coq_tests -v
```

The Coq/SQIR backend checks Bell, GHZ(3), and the two fixed Deutsch-Jozsa
examples. Follow the [pinned Coq setup](docs/DEVELOPMENT.md#coq-environment),
then run `opam exec -- python -m pytest coq_tests -v`. CI compiles the committed
modules, rejects mutated DJ targets, and checks generated `.v` files for drift.
Generated Coq proofs use the gate language, SQIR translation, and proof tactic
defined in `coq/QuantumValidation/Circuit.v`. The Coq gate regression checks
176 exact gate/basis obligations, plus 14 empty-circuit cases and 3 complex
amplitudes. I, X, Z, and CNOT reach three qubits; H and SWAP stop at two because
their dimension-eight proof terms exceed the pinned QuantumLib tactic budget.
The Python CI job also checks generated Lean source for drift for Bell, GHZ(3),
DJ constant, and DJ balanced on both Linux and Windows.

See [architecture](docs/ARCHITECTURE.md), the
[code study guide](docs/CODE_STUDY_GUIDE.md),
[development](docs/DEVELOPMENT.md), and the
[formal trust boundary](docs/TRUST_BOUNDARY.md). Reviewers can use the
[show-off command guide](docs/SHOWOFF_GUIDE.md) for a live demo, the
[presentation guide](docs/PRESENTATION_GUIDE.md) for the main claims, and the
[Coq/SQIR guide](docs/COQ_SQIR.md) for the second formal backend.

For a short demonstration of why basis measurements are insufficient, run
`fqv-demo-phase`. It exhibits a relative-phase mutation whose measurement
probabilities pass while the exact-state contract fails as intended. The
[phase demo guide](docs/PHASE_DEMO.md) includes the complete expected output
and explains why the command treats this rejection as success.
