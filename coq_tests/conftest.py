"""Compile the shared Coq abstraction once, then test clients in isolation."""

import shutil
import subprocess
from collections.abc import Callable
from functools import partial
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CoqCompiler = Callable[[str, Path], subprocess.CompletedProcess[str]]


def compile_source(
    source: str, destination: Path, *, library: Path,
) -> subprocess.CompletedProcess[str]:
    """Use a fresh output path and only this session's compiled Circuit module."""
    compiler = shutil.which("coqc")
    assert compiler is not None, "Run coq/setup.sh inside the pinned opam switch first"
    destination.write_text(source, encoding="utf-8", newline="\n")
    return subprocess.run(
        [compiler, "-R", str(ROOT / "build/SQIR/SQIR"), "SQIR",
         "-Q", str(library), "QuantumValidation", str(destination)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=600, check=False, cwd=destination.parent,
    )


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


@pytest.fixture(scope="session")
def coq_compile(tmp_path_factory: pytest.TempPathFactory) -> CoqCompiler:
    """Compile the shared abstraction once and isolate every generated client."""

    require_pinned_compiler()
    library = tmp_path_factory.mktemp("coq_library")
    compile_client = partial(compile_source, library=library)
    source = (ROOT / "coq/QuantumValidation/Circuit.v").read_text("utf-8")
    result = compile_client(source, library / "Circuit.v")
    assert result.returncode == 0, result.stdout + result.stderr
    return compile_client
