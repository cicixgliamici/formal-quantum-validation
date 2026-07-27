from __future__ import annotations

import argparse
from pathlib import Path

from fqv.bell import (
    bell_contract,
    build_bell_circuit,
)
from fqv.checks import verify_contract
from fqv.ir import export_ir
from fqv.transpilation import (
    TranspilationConfig,
    transpile_and_check,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify the Bell-state MVP 0 contract."
        )
    )

    parser.add_argument(
        "--shots",
        type=int,
        default=4096,
        help=(
            "number of sampled computational-basis "
            "measurements"
        ),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="random seed used for sampling",
    )

    parser.add_argument(
        "--ir-output",
        type=Path,
        default=Path("build/bell_ir.json"),
        help="destination for the circuit IR",
    )

    parser.add_argument(
        "--json-report",
        type=Path,
        default=None,
        help=(
            "optional destination for the "
            "verification report"
        ),
    )

    parser.add_argument(
        "--transpile",
        action="store_true",
        help=(
            "transpile deterministically and check complete "
            "operator equivalence"
        ),
    )

    parser.add_argument(
        "--optimization-level",
        type=int,
        choices=range(4),
        default=1,
        help="Qiskit transpiler optimization level",
    )

    parser.add_argument(
        "--seed-transpiler",
        type=int,
        default=7,
        help="seed used by stochastic transpiler passes",
    )

    parser.add_argument(
        "--transpiled-ir-output",
        type=Path,
        default=Path("build/bell_transpiled_ir.json"),
        help="destination for the transpiled circuit IR",
    )

    parser.add_argument(
        "--equivalence-report",
        type=Path,
        default=None,
        help="optional destination for transpilation evidence",
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    circuit = build_bell_circuit()
    contract = bell_contract()

    report = verify_contract(
        circuit,
        contract,
        shots=args.shots,
        seed=args.seed,
    )

    ir_path = export_ir(
        circuit,
        args.ir_output,
    )

    print(report.render_text())
    print()
    print(f"IR written to: {ir_path}")

    equivalence_passed = True
    if args.transpile:
        transpiled, equivalence = transpile_and_check(
            circuit,
            config=TranspilationConfig(
                optimization_level=args.optimization_level,
                seed_transpiler=args.seed_transpiler,
            ),
        )
        transpiled_ir_path = export_ir(
            transpiled,
            args.transpiled_ir_output,
        )
        equivalence_passed = equivalence.passed

        print()
        print(equivalence.render_text())
        print(
            f"Transpiled IR written to: "
            f"{transpiled_ir_path}"
        )

        if args.equivalence_report is not None:
            args.equivalence_report.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            args.equivalence_report.write_text(
                equivalence.to_json() + "\n",
                encoding="utf-8",
            )
            print(
                f"Equivalence report written to: "
                f"{args.equivalence_report}"
            )

    if args.json_report is not None:
        args.json_report.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        args.json_report.write_text(
            report.to_json() + "\n",
            encoding="utf-8",
        )

        print(
            f"JSON report written to: "
            f"{args.json_report}"
        )

    return 0 if report.passed and equivalence_passed else 1
