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

from fqv.domain.contract_parser import load_contract
from fqv.frontend.qiskit.conversion import checked_ir_to_qiskit
from fqv.frontend.qiskit.extraction import export_ir
from fqv.frontend.qiskit.verification import verify_contract
from fqv.ir.raw import load_raw_ir
from fqv.ir.validation import check_ir
from fqv.pipeline.transpilation import (
    TranspilationConfig,
    transpile_and_check,
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
        default=Path("examples/bell_ir.json"),
        help="source circuit IR",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("src/fqv/data/bell.contract.json"),
        help="executable quantum contract",
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
    # Input path: raw.py reads JSON, validation.py creates trusted core IR,
    # and conversion.py is the first layer allowed to construct Qiskit data.
    # Raw JSON has no trusted meaning until `check_ir` returns successfully.
    checked_ir = check_ir(load_raw_ir(args.ir))
    circuit = checked_ir_to_qiskit(checked_ir)
    contract = load_contract(args.contract)
    # Detect the cross-document mismatch before Qiskit reports a lower-level
    # statevector dimension error.
    if checked_ir.num_qubits != contract.num_qubits:
        raise ValueError(
            f"circuit has {checked_ir.num_qubits} qubits but contract "
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
    if args.transpile:
        # This optional branch returns here after transpiling and comparing the
        # complete operators; extraction.py then serializes the checked result.
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

    if args.json_report is not None:
        _write_report(args.json_report, report)

    return 0 if report.passed and equivalence_passed else 1
