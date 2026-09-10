"""Keep every committed generated Coq obligation tied to its JSON inputs."""

import json
from pathlib import Path

import pytest

from fqv.backend.coq.generator import generate_coq_module


ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ("bell", "GeneratedBell"),
    ("ghz3", "GeneratedGhz3"),
    ("dj2_constant", "GeneratedDj2Constant"),
    ("dj2_balanced", "GeneratedDj2Balanced"),
]


@pytest.mark.parametrize("example,module", CASES)
def test_committed_coq_matches_generator(example: str, module: str) -> None:
    ir = json.loads((ROOT / f"examples/{example}_ir.json").read_text("utf-8"))
    contract = json.loads(
        (ROOT / f"src/fqv/data/{example}.contract.json").read_text("utf-8")
    )
    committed = ROOT / f"coq/QuantumValidation/{module}.v"
    # Byte comparison also detects encoding and newline drift.
    assert committed.read_bytes() == generate_coq_module(ir, contract).source.encode("utf-8")


def test_all_generated_modules_have_drift_coverage() -> None:
    assert {path.stem for path in (ROOT / "coq/QuantumValidation").glob("Generated*.v")} == {
        module for _, module in CASES
    }
