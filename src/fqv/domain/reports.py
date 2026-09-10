"""Qiskit-independent reports emitted by verification stages."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class CheckResult:
    """Immutable evidence emitted by one independently understandable check.

    `details` is intended for a reviewer reading terminal output. `data` keeps
    the same evidence machine-readable for CI, experiments, and future report
    schema versioning.

    A frontend check computes the verdict and constructs this object; it then
    calls VerificationReport.add. Serialization preserves the computed result
    and never reruns the check. This is executable evidence, not a Lean proof.
    """

    name: str
    passed: bool
    details: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return stable JSON-compatible evidence for this check."""

        return asdict(self)


@dataclass
class VerificationReport:
    """Ordered collection of executable contract-check results.

    The report contains no verification policy beyond conjunction: it passes
    exactly when every recorded check passes. This makes the result easy to
    explain and prevents hidden success criteria inside the renderer.

    verification.verify_contract creates one report and passes the same object
    through structure, state, exact-probability, and sampling checks. The
    pipeline returns it to cli.main, which renders it and selects an exit code.
    An empty report has a vacuously true `passed` property; only a completed
    verification workflow supplies the obligations needed for a useful verdict.
    """

    contract_name: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Require every recorded obligation to pass."""

        return all(check.passed for check in self.checks)

    def add(self, result: CheckResult) -> None:
        """Append evidence in execution order for readable diagnostics."""

        self.checks.append(result)

    def to_dict(self) -> dict[str, Any]:
        """Return the complete aggregate as JSON-compatible data."""

        return {
            "contract_name": self.contract_name,
            "passed": self.passed,
            "checks": [check.to_dict() for check in self.checks],
        }

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize deterministically for CI and experiment artifacts."""

        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    def render_text(self) -> str:
        """Render a reviewer-friendly summary without changing policy."""

        overall = "PASS" if self.passed else "FAIL"
        lines = [
            f"Contract: {self.contract_name}",
            f"Overall result: {overall}",
            "",
        ]
        for check in self.checks:
            marker = "PASS" if check.passed else "FAIL"
            lines.append(f"[{marker}] {check.name}: {check.details}")
        return "\n".join(lines)


@dataclass(frozen=True)
class EquivalenceReport:
    """Numerical evidence about preservation of a complete circuit operator.

    This is executable evidence produced by Qiskit and NumPy, not a formal
    proof. The report records both a global-phase-independent fidelity and a
    directly interpretable phase-aligned matrix error.

    pipeline.transpilation.check_operator_equivalence constructs this after
    Qiskit builds both complete operators. cli.main consumes its verdict and
    optionally writes JSON. Gate counts and depths describe the compared
    circuits, not a proof that the chosen optimization is optimal. A PASS
    allows global phase and therefore does not imply exact IR exportability
    or satisfaction of the separate exact-vector state contract.
    """

    passed: bool
    process_fidelity: float
    threshold: float
    equivalent_up_to_global_phase: bool
    max_phase_aligned_error: float
    source_depth: int
    transpiled_depth: int
    source_gate_counts: dict[str, int]
    transpiled_gate_counts: dict[str, int]
    optimization_level: int
    seed_transpiler: int
    basis_gates: tuple[str, ...]
    layout_applied: bool

    def to_dict(self) -> dict[str, Any]:
        """Return all numerical evidence and reproducibility settings."""

        return asdict(self)

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize the evidence with deterministic key ordering."""

        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    def render_text(self) -> str:
        """Render the semantic verdict before optimization metrics."""

        result = "PASS" if self.passed else "FAIL"
        return "\n".join(
            [
                f"Transpilation equivalence: {result}",
                f"Process fidelity: {self.process_fidelity:.15f}",
                (
                    "Equivalent up to global phase: "
                    f"{self.equivalent_up_to_global_phase}"
                ),
                (
                    "Maximum phase-aligned error: "
                    f"{self.max_phase_aligned_error:.3e}"
                ),
                f"Depth: {self.source_depth} -> {self.transpiled_depth}",
            ]
        )
