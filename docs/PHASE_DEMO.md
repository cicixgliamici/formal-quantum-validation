# Relative-phase failure demonstration

This demonstration shows why computational-basis measurement probabilities do
not uniquely determine a quantum state. It is intentionally short and is a
useful opening example for a live presentation.

## Run the demonstration

After installing the project, run:

```powershell
fqv-demo-phase
```

The module form is equivalent and is useful in a development checkout where
the console entry point has not yet been reinstalled:

```powershell
python -m fqv.failure_demo
```

Both commands accept `--shots` and `--seed`. The defaults are 4096 shots and
seed 7; keeping them unchanged makes the sampled check reproducible.

## Expected terminal output

```text
Relative-phase failure showcase
Circuit: Bell Phi-minus; contract: Bell Phi-plus

Measurement probabilities: PASS
Exact quantum state: FAIL
State diagnostic: fidelity=0.000000000000, amplitudes-match=False, max-amplitude-error=1.41

Conclusion: computational-basis probabilities agree, but the relative
phase changes the quantum state and the exact contract rejects it.
```

The exact and sampled probabilities pass because both Bell states assign
probability `1/2` to `00` and `11`, and zero to the other computational-basis
outcomes. Their amplitudes differ in the sign of the `11` component:

```text
Phi-plus  = (|00> + |11>) / sqrt(2)
Phi-minus = (|00> - |11>) / sqrt(2)
```

Consequently, the states are orthogonal and their fidelity is zero. The exact
state contract detects the relative-phase error even though measurement in the
computational basis does not.

## Meaning of the exit code

Exit code `0` means that the intended contrast was observed:

- every exact and sampled probability check passed;
- exact-state equality failed as expected.

A nonzero exit code means that the demonstration did not produce this expected
combination. The displayed `FAIL` is therefore a successful detection, not a
failed demonstration.

## Scope of the evidence

This command provides executable Qiskit evidence, not a Lean or Coq proof. Its
purpose is to motivate exact-state contracts. Formal transpilation evidence is
generated separately with `fqv-verify --transpile` and either the Lean or Coq
proof backend.
