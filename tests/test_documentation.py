"""Keep reviewer-facing Markdown navigation valid as the repository evolves."""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
MARKDOWN_LINK = re.compile(r"\[[^]]+]\(([^)]+)\)")


def _markdown_files() -> list[Path]:
    """Return committed reviewer-facing Markdown rather than local planning."""

    return [PROJECT_ROOT / "README.md", *sorted((PROJECT_ROOT / "docs").glob("*.md"))]


def _local_target(document: Path, raw_target: str) -> Path | None:
    """Resolve local links while leaving network availability outside CI."""

    target = raw_target.strip("<>").split("#", 1)[0]
    if not target or "://" in target:
        return None
    return document.parent / target


def test_all_local_markdown_links_resolve() -> None:
    """Prevent documentation refactors from leaving broken repository links."""

    missing = [
        (document.relative_to(PROJECT_ROOT), target)
        for document in _markdown_files()
        for raw_target in MARKDOWN_LINK.findall(document.read_text(encoding="utf-8"))
        if (target := _local_target(document, raw_target)) is not None
        if not target.exists()
    ]
    assert not missing, f"Broken local Markdown links: {missing}"
