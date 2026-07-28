"""Exact and sampled computational-basis probability checks."""

from __future__ import annotations

from collections.abc import Mapping

from qiskit.quantum_info import Statevector

from fqv.domain.contracts import QuantumContract
from fqv.domain.reports import CheckResult, VerificationReport


def _plain_counts(values: Mapping[object, object]) -> dict[str, int]:
    return {
        str(key): int(value)
        for key, value in values.items()
    }


def check_exact_probabilities(
    state: Statevector,
    contract: QuantumContract,
    report: VerificationReport,
) -> None:
    """Check ideal computational-basis probabilities."""

    # Missing outcomes have probability zero, so sparse Qiskit dictionaries
    # can be compared directly with explicit contract expectations.
    probabilities = {
        str(outcome): float(probability)
        for outcome, probability in state.probabilities_dict().items()
    }
    for expectation in contract.probabilities:
        observed = probabilities.get(expectation.outcome, 0.0)
        difference = abs(observed - expectation.expected)
        report.add(
            CheckResult(
                name=f"exact-probability:{expectation.outcome}",
                passed=difference <= expectation.exact_tolerance,
                details=(
                    f"expected {expectation.expected:.6f}, "
                    f"observed {observed:.6f}"
                ),
                data={
                    "outcome": expectation.outcome,
                    "expected": expectation.expected,
                    "observed": observed,
                    "difference": difference,
                    "tolerance": expectation.exact_tolerance,
                },
            )
        )


def check_sampled_probabilities(
    state: Statevector,
    contract: QuantumContract,
    report: VerificationReport,
    *,
    shots: int,
    seed: int,
) -> None:
    """Check reproducible sampled computational-basis frequencies."""

    # Seeding the Statevector sampler makes CI evidence reproducible. These
    # frequencies remain statistical observations, not formal guarantees.
    state.seed(seed)
    counts = _plain_counts(state.sample_counts(shots))
    for expectation in contract.probabilities:
        observed_count = counts.get(expectation.outcome, 0)
        observed = observed_count / shots
        difference = abs(observed - expectation.expected)
        report.add(
            CheckResult(
                name=f"sampled-probability:{expectation.outcome}",
                passed=difference <= expectation.sampled_tolerance,
                details=(
                    f"expected {expectation.expected:.3f}, "
                    f"observed {observed:.3f} ({observed_count}/{shots})"
                ),
                data={
                    "outcome": expectation.outcome,
                    "expected": expectation.expected,
                    "observed": observed,
                    "count": observed_count,
                    "shots": shots,
                    "seed": seed,
                    "difference": difference,
                    "tolerance": expectation.sampled_tolerance,
                },
            )
        )
