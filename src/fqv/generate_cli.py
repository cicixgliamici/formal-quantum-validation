from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from fqv.ir_validation import load_ir
from fqv.lean_generator import write_lean_module


def _load_json_object(path: Path) -> dict[str, Any]:
    """Load an object while preserving validation in the domain layer."""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")

    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a Lean proof obligation from circuit IR "
            "and a shared contract."
        )
    )
    parser.add_argument("ir", type=Path)
    parser.add_argument("contract", type=Path)
    parser.add_argument("output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    ir = load_ir(args.ir)
    contract_data = _load_json_object(args.contract)
    output = write_lean_module(
        ir,
        contract_data,
        args.output,
    )
    print(f"Lean module written to: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
