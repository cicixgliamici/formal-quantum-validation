"""Raw JSON-compatible circuit IR types and file loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypeAlias

RawOperation: TypeAlias = dict[str, Any]
RawCircuitIr: TypeAlias = dict[str, Any]


def load_raw_ir(path: str | Path) -> RawCircuitIr:
    """Load IR JSON without assigning it trusted domain meaning.

    Both CLIs call this before check_ir. This function checks only JSON syntax
    and an object root: successful loading does not establish schema validity,
    gate arity, or register bounds. Consumers must not bypass check_ir.
    """

    ir_path = Path(path)
    raw = json.loads(ir_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("circuit IR must be a JSON object")
    return raw
