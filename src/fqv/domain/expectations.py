"""Domain expectations evaluated by verification pipelines."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProbabilityExpectation:
    """One observable probability requirement and its two tolerances.

    Exact and sampled checks intentionally use different tolerances. Numerical
    statevector evaluation should be close to machine precision, whereas a
    finite-shot experiment has sampling variation.

    contract_parser._parse_expectations creates one object per declared outcome.
    checks.probabilities reads it twice: first against ideal state probabilities,
    then against sample_counts from that same Statevector. Both comparisons
    append separate CheckResult objects. Sampling is simulated, not hardware
    evidence, and a sampled tolerance is not a statistical confidence level.

    Outcome strings display the highest-index qubit on the left: "01" means
    qubit 0 is one and qubit 1 is zero. Outcomes omitted by a contract do not
    receive individual probability checks; the target-state check is separate.
    """

    outcome: str
    expected: float
    exact_tolerance: float = 1e-12
    sampled_tolerance: float = 0.05
