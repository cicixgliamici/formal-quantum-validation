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
    """Compile one client against the Circuit module built by this test session.

    Writing every source to a pytest directory prevents a committed `.vo` file
    or a previous local build from satisfying an import accidentally. Returning
    the process instead of raising lets negative tests inspect genuine Coq
    rejection while still distinguishing it from Python-side failures.
    """
    compiler = shutil.which("coqc")
    assert compiler is not None, "Run coq/setup.sh inside the pinned opam switch first"
    destination.write_text(source, encoding="utf-8", newline="\n")
    # -R exposes the pinned SQIR checkout; -Q gives the fresh Circuit artifact
    # the same logical name imported by generated production modules.
    return subprocess.run(
        [compiler, "-R", str(ROOT / "build/SQIR/SQIR"), "SQIR",
         "-Q", str(library), "QuantumValidation", str(destination)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=600, check=False, cwd=destination.parent,
    )


def require_pinned_compiler() -> None:
    """Reject an available but unpinned compiler before running semantic tests."""
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
    """Build Circuit.v once, then return a compiler bound to that fresh library.

    Circuit.v is shared by every generated client, so session scope avoids
    repeating its compilation without allowing clients to share definitions or
    theorem names with one another.
    """

    require_pinned_compiler()
    library = tmp_path_factory.mktemp("coq_library")
    compile_client = partial(compile_source, library=library)
    # Compile the source copied into the temporary logical library. Client
    # imports must resolve this artifact, never a repository-local Circuit.vo.
    source = (ROOT / "coq/QuantumValidation/Circuit.v").read_text("utf-8")
    result = compile_client(source, library / "Circuit.v")
    assert result.returncode == 0, result.stdout + result.stderr
    return compile_client
