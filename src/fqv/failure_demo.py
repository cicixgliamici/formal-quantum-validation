"""Reviewer-facing demonstration of information hidden by measurement counts."""

from __future__ import annotations

import argparse

from fqv.domain.reports import VerificationReport
from fqv.frontend.qiskit.checks.probabilities import (
    check_exact_probabilities,
    check_sampled_probabilities,
)
from fqv.frontend.qiskit.checks.state import check_target_state
from fqv.frontend.qiskit.circuits import bell_contract, build_bell_minus_circuit


def build_parser() -> argparse.ArgumentParser:
    """Expose sampling controls so the live demonstration is reproducible."""

    parser = argparse.ArgumentParser(
        description="Show a relative-phase error hidden by basis probabilities."
    )
    parser.add_argument("--shots", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=7)
    return parser


def _render_contrast(report: VerificationReport) -> str:
    """Render only the evidence needed to explain the semantic contrast."""

    state_check = next(check for check in report.checks if check.name == "target-state")
    probability_checks = [
        check for check in report.checks if "probability:" in check.name
    ]
    probabilities_pass = all(check.passed for check in probability_checks)
    return "\n".join(
        [
            "Relative-phase failure showcase",
            "Circuit: Bell Phi-minus; contract: Bell Phi-plus",
            "",
            f"Measurement probabilities: {'PASS' if probabilities_pass else 'FAIL'}",
            f"Exact quantum state: {'PASS' if state_check.passed else 'FAIL'}",
            f"State diagnostic: {state_check.details}",
            "",
            "Conclusion: computational-basis probabilities agree, but the relative",
            "phase changes the quantum state and the exact contract rejects it.",
        ]
    )


def main() -> int:
    """Return success only when the intended hidden-phase contrast is observed."""

    args = build_parser().parse_args()
    contract = bell_contract()
    report = VerificationReport(contract_name=contract.name)
    # Structure is deliberately omitted: the demonstration isolates semantic
    # observations so the additional Z gate cannot distract with a resource
    # mismatch before the relative-phase distinction is shown.
    state = check_target_state(build_bell_minus_circuit(), contract, report)
    check_exact_probabilities(state, contract, report)
    check_sampled_probabilities(
        state,
        contract,
        report,
        shots=args.shots,
        seed=args.seed,
    )
    print(_render_contrast(report))

    # The state rejection is the expected outcome, so the command succeeds
    # only when probability checks pass and exact-state checking catches it.
    state_failed = not report.checks[0].passed
    probabilities_passed = all(check.passed for check in report.checks[1:])
    return 0 if state_failed and probabilities_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
