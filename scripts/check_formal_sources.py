"""Enforce the project's Lean source policy without requiring a Lean toolchain."""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_TOKEN = re.compile(r"\b(?:sorry|admit|sorryAx|axiom|opaque)\b")


def mask_noncode(source: str) -> str:
    """Blank comments and strings while preserving diagnostic line numbers.

    Lean block comments nest. A flat regular expression would miss code after
    an inner comment and could let a real placeholder pass unnoticed.
    """

    masked = list(source)
    position = 0
    comment_depth = 0
    in_string = False
    while position < len(source):
        start = position
        pair = source[position:position + 2]
        if comment_depth:
            if pair == "/-":
                comment_depth += 1
                position += 2
            elif pair == "-/":
                comment_depth -= 1
                position += 2
            else:
                position += 1
        elif in_string:
            if source[position] == "\\":
                position = min(position + 2, len(source))
            else:
                in_string = source[position] != '"'
                position += 1
        elif pair == "/-":
            comment_depth = 1
            position += 2
        elif pair == "--":
            end = source.find("\n", position)
            position = len(source) if end == -1 else end
        elif source[position] == '"':
            in_string = True
            position += 1
        else:
            position += 1
            continue
        # Preserve newlines so a rejected token points to its original source line.
        for index in range(start, position):
            if masked[index] != "\n":
                masked[index] = " "
    return "".join(masked)


def policy_violations(source: str) -> list[tuple[int, str]]:
    """Find prohibited tokens; this is a source guard, not an assumptions audit."""

    code = mask_noncode(source)
    return [
        (code.count("\n", 0, match.start()) + 1, match.group())
        for match in FORBIDDEN_TOKEN.finditer(code)
    ]


def main() -> int:
    """Check project-owned Lean sources, excluding downloaded dependencies."""

    paths = sorted((PROJECT_ROOT / "lean").rglob("*.lean"))
    if not paths:
        raise RuntimeError("No project Lean sources found")
    failures = [
        f"{path.relative_to(PROJECT_ROOT)}:{line}: prohibited token {token}"
        for path in paths
        for line, token in policy_violations(path.read_text(encoding="utf-8"))
    ]
    if failures:
        print("\n".join(failures))
        return 1
    print(f"Lean source policy passed for {len(paths)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
