"""Check that the CI guard catches placeholders without flagging prose."""

from __future__ import annotations

import pytest

from scripts import check_formal_sources
from scripts.check_formal_sources import main, policy_violations


@pytest.mark.parametrize(
    "source, token",
    [
        ("theorem unchecked : True := by sorry", "sorry"),
        ("theorem unchecked : True := by\n  admit", "admit"),
        ("axiom unchecked : False", "axiom"),
        ("opaque unchecked : Nat", "opaque"),
        ("theorem unchecked : False := sorryAx False true", "sorryAx"),
        ("/- outer /- inner -/ -/\nsorry", "sorry"),
        ('/- a quote " does not start a string -/\nsorry', "sorry"),
    ],
)
def test_rejects_proof_shortcuts(source: str, token: str) -> None:
    findings = policy_violations(source)
    assert len(findings) == 1
    assert findings[0] == (source.count("\n") + 1, token)


@pytest.mark.parametrize(
    "source",
    [
        "-- no sorry, axiom, or opaque declarations\ntheorem checked : True := by trivial",
        "/- outer /- sorry -/ opaque -/ theorem checked : True := by trivial",
        'def description := "sorry /- axiom -/ -- opaque"',
        'def description := "escaped \\" sorry"',
        "def sorryCount : Nat := 0",
    ],
)
def test_allows_comments_strings_and_longer_names(source: str) -> None:
    assert policy_violations(source) == []


def test_project_lean_sources_follow_policy() -> None:
    """Run the same policy locally and in both Python CI matrix entries."""

    assert main() == 0


def test_policy_command_fails_on_mutated_source(tmp_path, monkeypatch, capsys) -> None:
    """Ensure CI gets a failing exit code and the location of a real mutation."""

    source_directory = tmp_path / "lean"
    source_directory.mkdir()
    (source_directory / "Mutated.lean").write_text(
        "theorem unchecked : True := by\n  sorry\n", encoding="utf-8"
    )
    monkeypatch.setattr(check_formal_sources, "PROJECT_ROOT", tmp_path)
    assert main() == 1
    assert "Mutated.lean:2: prohibited token sorry" in capsys.readouterr().out
