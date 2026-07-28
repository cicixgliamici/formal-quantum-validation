"""Domain expectations evaluated by verification pipelines."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProbabilityExpectation:
    """One observable probability requirement and its two tolerances.

    Exact and sampled checks intentionally use different tolerances. Numerical
    statevector evaluation should be close to machine precision, whereas a
    finite-shot experiment has sampling variation.
    """

    outcome: str
    expected: float
    exact_tolerance: float = 1e-12
    sampled_tolerance: float = 0.05
