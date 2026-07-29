"""Provider-neutral hand-off between a caller and executable verification.

``fqv.cli`` calls :func:`verify` with a concrete verifier. The function then
calls that injected frontend (currently
``frontend.qiskit.verification.verify_contract``), which calls the individual
checks and returns a domain report through this module to the CLI.
"""

from __future__ import annotations

from typing import Protocol

from fqv.domain.contracts import QuantumContract
from fqv.domain.reports import VerificationReport


class ContractVerifier(Protocol):
    """Minimal dependency-inversion boundary for executable verification.

    The pipeline knows the domain contract and report but not the concrete
    circuit provider. Qiskit satisfies this protocol today; another simulator
    can be injected later without changing orchestration policy.
    """

    def __call__(
        self,
        circuit: object,
        contract: QuantumContract,
        *,
        shots: int,
        seed: int,
    ) -> VerificationReport: ...


def verify(
    circuit: object,
    contract: QuantumContract,
    *,
    verifier: ContractVerifier,
    shots: int = 4096,
    seed: int = 7,
) -> VerificationReport:
    """Run an injected frontend without coupling the pipeline to Qiskit.

    This small function is intentionally policy-only. It forwards reproducible
    sampling parameters and leaves individual scientific checks to the
    frontend implementation.
    """

    return verifier(
        circuit,
        contract,
        shots=shots,
        seed=seed,
    )
