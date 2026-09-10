"""Compile real obligations; missing Coq or SQIR is a failure, never a skip."""

import json
from pathlib import Path

import pytest

from fqv.backend.coq.generator import generate_coq_module


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("module", [
    "GeneratedBell", "GeneratedGhz3", "GeneratedDj2Constant",
    "GeneratedDj2Balanced",
])
def test_committed_module_compiles(module: str, tmp_path: Path, coq_compile) -> None:
    source = (ROOT / f"coq/QuantumValidation/{module}.v").read_text("utf-8")
    result = coq_compile(source, tmp_path / f"{module}.v")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("example", ["dj2_constant", "dj2_balanced"])
def test_coq_rejects_mutated_dj_target(example: str, tmp_path: Path, coq_compile) -> None:
    ir = json.loads((ROOT / f"examples/{example}_ir.json").read_text("utf-8"))
    contract = json.loads(
        (ROOT / f"src/fqv/data/{example}.contract.json").read_text("utf-8")
    )
    original = generate_coq_module(ir, contract).source
    control = coq_compile(original, tmp_path / "Control.v")
    assert control.returncode == 0, control.stdout + control.stderr
    # Flip one branch, preserving normalization but changing the relative phase.
    index = contract["target_state"].index("minus_inv_sqrt_two")
    contract["target_state"][index] = "inv_sqrt_two"
    mutated = generate_coq_module(ir, contract).source
    assert mutated != original
    # First compile the mutated definitions alone: syntax/import failures must
    # never count as evidence that Coq rejected a false theorem.
    definitions = mutated.split("Theorem ", 1)[0]
    syntax = coq_compile(definitions, tmp_path / "Definitions.v")
    assert syntax.returncode == 0, syntax.stdout + syntax.stderr
    result = coq_compile(mutated, tmp_path / "Mutated.v")
    assert result.returncode != 0, "Coq accepted a false DJ target"
    assert "Error:" in result.stdout + result.stderr
