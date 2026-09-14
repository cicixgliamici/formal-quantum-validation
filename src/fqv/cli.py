"""Command-line entry point for executable verification.

Call flow:
    ``python -m fqv`` -> ``fqv.__main__`` -> this module -> IR and contract
    parsers -> Qiskit conversion -> ``pipeline.verify`` -> Qiskit checks.

If requested, this module then calls the transpilation pipeline and sends both
the original and transpiled circuits to the IR exporter. Reports return here
for terminal rendering or JSON output, so lower layers never own CLI policy.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from fqv.backend.coq.transpilation import write_transpilation_coq_module
from fqv.backend.lean.transpilation import write_transpilation_lean_module
from fqv.domain.contract_parser import load_contract
from fqv.evidence_manifest import write_verification_manifest
from fqv.frontend.qiskit.circuits import bell_contract, build_bell_circuit
from fqv.frontend.qiskit.conversion import checked_ir_to_qiskit
from fqv.frontend.qiskit.extraction import circuit_to_ir, export_ir
from fqv.frontend.qiskit.verification import verify_contract
from fqv.ir.raw import load_raw_ir
from fqv.ir.validation import check_ir
from fqv.pipeline.transpilation import (
    TranspilationConfig,
    transpile_and_check,
)
from fqv.pipeline.transpilation_certificate import (
    certify_self_inverse_cancellations,
    write_transpilation_certificate,
)
from fqv.pipeline.verify import verify


def build_parser() -> argparse.ArgumentParser:
    """Build options shared by every supported circuit contract."""

    parser = argparse.ArgumentParser(
        description="Verify a checked circuit IR against a contract."
    )
    parser.add_argument(
        "--ir",
        type=Path,
        default=None,
        help="source circuit IR (default: packaged Bell example)",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=None,
        help="executable quantum contract (default: packaged Bell contract)",
    )
    parser.add_argument("--shots", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--ir-output",
        type=Path,
        default=None,
        help="optional normalized IR output",
    )
    parser.add_argument("--json-report", type=Path, default=None)
    parser.add_argument(
        "--verification-manifest",
        type=Path,
        default=None,
        help="optional provenance manifest for the complete run",
    )
    parser.add_argument("--transpile", action="store_true")
    parser.add_argument(
        "--optimization-level",
        type=int,
        choices=range(4),
        default=1,
    )
    parser.add_argument("--seed-transpiler", type=int, default=7)
    parser.add_argument(
        "--transpiled-ir-output",
        type=Path,
        default=Path("build/transpiled_ir.json"),
    )
    parser.add_argument("--equivalence-report", type=Path, default=None)
    parser.add_argument("--transpilation-certificate", type=Path, default=None)
    parser.add_argument("--transpilation-proof-output", type=Path, default=None)
    parser.add_argument(
        "--transpilation-proof-backend",
        choices=["lean", "coq"],
        default="lean",
    )
    return parser


def _write_report(path: Path, report: object) -> None:
    """Write one report exposing the stable `to_json` protocol.

    Keeping report I/O here prevents domain report classes from acquiring file
    system responsibilities.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    to_json = getattr(report, "to_json")
    path.write_text(to_json() + "\n", encoding="utf-8")


def main() -> int:
    """Run verification for the IR and contract selected by the user.

    The command follows the architectural boundaries explicitly: load raw
    documents, validate into checked/domain objects, construct the selected
    frontend circuit, then invoke pipeline stages.
    """

    args = build_parser().parse_args()
    # Explicit input: raw.py loads JSON -> check_ir validates and freezes its
    # operations -> checked_ir_to_qiskit constructs the executable circuit.
    # With no path, the packaged Bell constructor provides the reference circuit
    # directly, so the installed command also works outside the checkout.
    circuit = build_bell_circuit()
    if args.ir is not None:
        circuit = checked_ir_to_qiskit(check_ir(load_raw_ir(args.ir)))
    contract = bell_contract() if args.contract is None else load_contract(args.contract)
    # Detect the cross-document mismatch before Qiskit reports a lower-level
    # statevector dimension error.
    if circuit.num_qubits != contract.num_qubits:
        raise ValueError(
            f"circuit has {circuit.num_qubits} qubits but contract "
            f"requires {contract.num_qubits}"
        )
    # Control passes through the provider-neutral pipeline boundary before
    # verification.py dispatches the individual Qiskit scientific checks.
    report = verify(
        circuit,
        contract,
        verifier=verify_contract,
        shots=args.shots,
        seed=args.seed,
    )

    print(report.render_text())
    if args.ir_output is not None:
        normalized_path = export_ir(circuit, args.ir_output)
        print(f"\nIR written to: {normalized_path}")

    equivalence_passed = True
    equivalence = None
    certificate = None
    certificate_path = None
    proof_path = None
    if args.transpile:
        # This branch compares complete operators, independently of the source
        # contract's one input state. Export then checks exact IR restrictions:
        # a numerical PASS up to phase does not make phase/layout exportable.
        transpiled, equivalence = transpile_and_check(
            circuit,
            config=TranspilationConfig(
                optimization_level=args.optimization_level,
                seed_transpiler=args.seed_transpiler,
            ),
        )
        transpiled_path = export_ir(
            transpiled,
            args.transpiled_ir_output,
        )
        equivalence_passed = equivalence.passed
        print(f"\n{equivalence.render_text()}")
        print(f"Transpiled IR written to: {transpiled_path}")
        if args.equivalence_report is not None:
            _write_report(args.equivalence_report, equivalence)

        formal_requested = (
            args.transpilation_certificate is not None
            or args.transpilation_proof_output is not None
        )
        if formal_requested:
            # Both endpoints cross the checked-IR boundary before the
            # provider-neutral recognizer proposes a formal proof trace.
            source_ir = check_ir(circuit_to_ir(circuit))
            candidate_ir = check_ir(circuit_to_ir(transpiled))
            certificate = certify_self_inverse_cancellations(source_ir, candidate_ir)
            if args.transpilation_certificate is not None:
                certificate_path = write_transpilation_certificate(
                    certificate,
                    args.transpilation_certificate,
                )
                print(f"Transpilation certificate written to: {certificate_path}")
            if args.transpilation_proof_output is not None:
                writer = (
                    write_transpilation_coq_module
                    if args.transpilation_proof_backend == "coq"
                    else write_transpilation_lean_module
                )
                proof_path = writer(certificate, args.transpilation_proof_output)
                print(f"Formal transpilation proof written to: {proof_path}")

    if args.json_report is not None:
        _write_report(args.json_report, report)

    if args.verification_manifest is not None:
        manifest_path = write_verification_manifest(
            args.verification_manifest,
            ir_path=args.ir,
            contract_path=args.contract,
            verification=report,
            equivalence=equivalence,
            certificate=certificate,
            certificate_path=certificate_path,
            proof_path=proof_path,
            proof_backend=(
                args.transpilation_proof_backend if proof_path is not None else None
            ),
        )
        print(f"Verification manifest written to: {manifest_path}")

    # Generation produces an obligation, while Lean or Coq remains responsible
    # for accepting it in the subsequent toolchain step.
    return 0 if report.passed and equivalence_passed else 1
