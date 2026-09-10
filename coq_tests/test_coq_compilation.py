"""Compile real obligations; missing Coq or SQIR is a failure, never a skip."""

import json
from pathlib import Path
import shutil
import subprocess

import pytest

from fqv.backend.coq.generator import generate_coq_module


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def require_pinned_compiler() -> None:
    """A successful build with a different compiler is not pin validation."""
    pins = dict(
        line.split("=", 1) for line in (ROOT / "coq/toolchain.env").read_text().splitlines()
        if line and not line.startswith("#")
    )
    compiler = shutil.which("coqc")
    assert compiler is not None, "Install the pinned Coq environment with coq/setup.sh"
    result = subprocess.run(
        [compiler, "--print-version"], capture_output=True, text=True,
        timeout=30, check=True,
    )
    assert result.stdout.split()[0] == pins["COQ_VERSION"]


def compile_source(source: str, destination: Path) -> subprocess.CompletedProcess[str]:
    compiler = shutil.which("coqc")
    assert compiler is not None, "Run coq/setup.sh inside the pinned opam switch first"
    destination.write_text(source, encoding="utf-8", newline="\n")
    # Compile in temporary directories so stale .vo files cannot mask a failure.
    return subprocess.run(
        [compiler, "-R", str(ROOT / "build/SQIR/SQIR"), "SQIR", str(destination)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=600, check=False, cwd=destination.parent,
    )


@pytest.mark.parametrize("module", [
    "Circuit", "GeneratedBell", "GeneratedGhz3", "GeneratedDj2Constant",
    "GeneratedDj2Balanced",
])
def test_committed_module_compiles(module: str, tmp_path: Path) -> None:
    source = (ROOT / f"coq/QuantumValidation/{module}.v").read_text("utf-8")
    result = compile_source(source, tmp_path / f"{module}.v")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("example", ["dj2_constant", "dj2_balanced"])
def test_coq_rejects_mutated_dj_target(example: str, tmp_path: Path) -> None:
    ir = json.loads((ROOT / f"examples/{example}_ir.json").read_text("utf-8"))
    contract = json.loads(
        (ROOT / f"src/fqv/data/{example}.contract.json").read_text("utf-8")
    )
    original = generate_coq_module(ir, contract).source
    control = compile_source(original, tmp_path / "Control.v")
    assert control.returncode == 0, control.stdout + control.stderr
    # Flip one branch, preserving normalization but changing the relative phase.
    index = contract["target_state"].index("minus_inv_sqrt_two")
    contract["target_state"][index] = "inv_sqrt_two"
    mutated = generate_coq_module(ir, contract).source
    assert mutated != original
    # First compile the mutated definitions alone: syntax/import failures must
    # never count as evidence that Coq rejected a false theorem.
    definitions = mutated.split("Theorem ", 1)[0]
    syntax = compile_source(definitions, tmp_path / "Definitions.v")
    assert syntax.returncode == 0, syntax.stdout + syntax.stderr
    result = compile_source(mutated, tmp_path / "Mutated.v")
    assert result.returncode != 0, "Coq accepted a false DJ target"
    assert "Error:" in result.stdout + result.stderr
