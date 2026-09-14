"""Recognize a small exact rewrite trace between two checked circuits."""

from __future__ import annotations

import json
from pathlib import Path

from fqv.domain.transpilation import (
    TranspilationCertificate,
    UnsupportedTranspilationError,
    certify_h_cancellations,
    certify_self_inverse_cancellations,
)

__all__ = [
    "UnsupportedTranspilationError",
    "certify_h_cancellations",
    "certify_self_inverse_cancellations",
    "write_transpilation_certificate",
]


def write_transpilation_certificate(
    certificate: TranspilationCertificate,
    destination: str | Path,
) -> Path:
    """Write a deterministic, backend-neutral certificate artifact."""

    output = Path(destination)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(certificate.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output
