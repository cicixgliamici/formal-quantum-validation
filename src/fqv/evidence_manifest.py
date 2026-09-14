"""Build a reproducible summary of one verification run."""

from __future__ import annotations

import hashlib
import json
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from fqv.domain.reports import EquivalenceReport, VerificationReport
from fqv.domain.transpilation import TranspilationCertificate


def _sha256(path: Path) -> str:
    """Hash exact artifact bytes so reviewers can identify the checked inputs."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact(path: Path | None, *, status: str) -> dict[str, Any] | None:
    """Describe an existing file without claiming more than its known status."""

    if path is None:
        return None
    return {
        "path": str(path),
        "sha256": _sha256(path),
        "status": status,
    }


def _package_version(distribution: str) -> str | None:
    """Keep manifest generation useful even from a partial development setup."""

    try:
        return version(distribution)
    except PackageNotFoundError:
        return None


def _read_optional(path: Path) -> str | None:
    """Read a small toolchain pin when the checkout is available."""

    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").strip()


def _coq_pins(path: Path) -> dict[str, str]:
    """Parse committed key-value pins without executing an external tool."""

    if not path.is_file():
        return {}
    return dict(
        line.split("=", maxsplit=1)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#") and "=" in line
    )


def write_verification_manifest(
    destination: Path,
    *,
    ir_path: Path | None,
    contract_path: Path | None,
    verification: VerificationReport,
    equivalence: EquivalenceReport | None = None,
    certificate: TranspilationCertificate | None = None,
    certificate_path: Path | None = None,
    proof_path: Path | None = None,
    proof_backend: str | None = None,
) -> Path:
    """Write provenance and verdicts while separating generation from proof."""

    project_root = Path(__file__).resolve().parents[2]
    certificate_evidence = _artifact(
        certificate_path,
        status="generated_replayable_not_kernel_checked",
    )
    if certificate_evidence is not None and certificate is not None:
        certificate_evidence["schema_version"] = certificate.schema_version

    payload = {
        "schema_version": "0.1",
        "passed": verification.passed and (equivalence is None or equivalence.passed),
        "inputs": {
            "ir": _artifact(ir_path, status="checked_input") if ir_path else None,
            "contract": (
                _artifact(contract_path, status="parsed_input")
                if contract_path
                else None
            ),
        },
        "verification": verification.to_dict(),
        "transpilation_equivalence": equivalence.to_dict() if equivalence else None,
        "certificate": certificate_evidence,
        "formal_proof": (
            {
                **(_artifact(proof_path, status="generated_not_kernel_checked") or {}),
                "backend": proof_backend,
            }
            if proof_path
            else None
        ),
        "toolchain": {
            "python": sys.version.split()[0],
            "fqv": _package_version("formal-quantum-validation"),
            "qiskit": _package_version("qiskit"),
            "lean": _read_optional(project_root / "lean-toolchain"),
            "coq": _coq_pins(project_root / "coq" / "toolchain.env"),
        },
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination
