from __future__ import annotations

from pathlib import Path

from fqv.cli import build_parser
from fqv.frontend.qiskit.conversion import checked_ir_to_qiskit
from fqv.frontend.qiskit.extraction import circuit_to_ir
from fqv.ir.raw import load_raw_ir
from fqv.ir.validation import check_ir


PROJECT_ROOT = Path(__file__).parents[1]


def test_checked_ir_round_trip_preserves_linear_order() -> None:
    raw = load_raw_ir(PROJECT_ROOT / "examples" / "bell_ir.json")
    checked = check_ir(raw)
    reconstructed = checked_ir_to_qiskit(checked)

    assert circuit_to_ir(reconstructed) == raw


def test_cli_accepts_arbitrary_ir_and_contract_paths() -> None:
    parser = build_parser()
    arguments = parser.parse_args(
        [
            "--ir",
            "examples/ghz3_ir.json",
            "--contract",
            "src/fqv/data/ghz3.contract.json",
        ]
    )

    assert arguments.ir.name == "ghz3_ir.json"
    assert arguments.contract.name == "ghz3.contract.json"


def test_core_and_lean_backend_have_no_qiskit_imports() -> None:
    independent_roots = [
        PROJECT_ROOT / "src" / "fqv" / "domain",
        PROJECT_ROOT / "src" / "fqv" / "ir",
        PROJECT_ROOT / "src" / "fqv" / "backend" / "lean",
    ]
    sources = "\n".join(
        path.read_text(encoding="utf-8")
        for root in independent_roots
        for path in root.glob("*.py")
    )

    assert "import qiskit" not in sources
    assert "from qiskit" not in sources
