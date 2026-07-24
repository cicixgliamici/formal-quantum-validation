from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from typing import Any


@dataclass(frozen=True)
class CheckResult:
    """Result of one verification obligation."""

    name: str
    passed: bool
    details: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationReport:
    """Aggregated verification report."""

    contract_name: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    def add(self, result: CheckResult) -> None:
        self.checks.append(result)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_name": self.contract_name,
            "passed": self.passed,
            "checks": [
                check.to_dict()
                for check in self.checks
            ],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(
            self.to_dict(),
            indent=indent,
            sort_keys=True,
        )

    def render_text(self) -> str:
        overall = "PASS" if self.passed else "FAIL"

        lines = [
            f"Contract: {self.contract_name}",
            f"Overall result: {overall}",
            "",
        ]

        for check in self.checks:
            marker = "PASS" if check.passed else "FAIL"

            lines.append(
                f"[{marker}] {check.name}: {check.details}"
            )

        return "\n".join(lines)
