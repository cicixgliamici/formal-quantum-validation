"""Command-line entry point for deterministic Lean source generation.

Call flow:
    ``fqv-generate-lean`` -> this module -> raw IR validation ->
    ``backend.lean.generator`` -> generated ``.lean`` file -> Lean compiler.

The compiler is intentionally a later external step. This command prepares a
proof obligation, while Lean remains responsible for accepting or rejecting
the generated theorem.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from fqv.backend.lean.generator import write_lean_module
from fqv.ir.raw import load_raw_ir
from fqv.ir.validation import check_ir


def _load_json_object(path: Path) -> dict[str, Any]:
    """Load an object while preserving validation in the domain layer."""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")

    return data


def build_parser() -> argparse.ArgumentParser:
    """Describe the three explicit artifacts used by Lean generation."""

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
    """Validate input documents and write one deterministic Lean module."""

    args = build_parser().parse_args()
    # Validate the shared IR before the backend sees it. The generator parses
    # the contract itself because its exact amplitude tokens are source data.
    ir = load_raw_ir(args.ir)
    check_ir(ir)
    contract_data = _load_json_object(args.contract)
    # Control now moves to backend/lean/generator.py and returns only after the
    # deterministic source file has been written.
    output = write_lean_module(
        ir,
        contract_data,
        args.output,
    )
    print(f"Lean module written to: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
