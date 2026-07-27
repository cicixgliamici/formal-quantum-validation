from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from fqv.contracts import InvalidContractError, contract_from_dict
from fqv.ir_validation import InvalidIrError, validate_ir


class UnsupportedFormalizationError(ValueError):
    """Raised when valid input exceeds the current Lean semantics."""


_LEAN_AMPLITUDES: dict[str, str] = {
    "zero": "0",
    "one": "1",
    "minus_one": "-1",
    "i": "Complex.I",
    "minus_i": "-Complex.I",
    "inv_sqrt_two": "invSqrtTwo",
    "minus_inv_sqrt_two": "-invSqrtTwo",
}


@dataclass(frozen=True)
class GeneratedLeanModule:
    """Lean source plus the stable names exposed by the module."""

    source: str
    theorem_name: str


def _lean_identifier(value: str) -> str:
    """Create a readable Lean identifier from an external contract name."""

    words = re.findall(r"[A-Za-z0-9]+", value)
    identifier = "".join(
        word[:1].upper() + word[1:]
        for word in words
    )

    if not identifier:
        raise UnsupportedFormalizationError(
            "contract name cannot produce a Lean identifier"
        )

    if identifier[0].isdigit():
        identifier = f"Contract{identifier}"

    return identifier


def _format_amplitudes(tokens: Sequence[object]) -> list[str]:
    """Translate exact contract amplitudes to Lean expressions."""

    expressions: list[str] = []
    for index, token in enumerate(tokens):
        if (
            not isinstance(token, str)
            or token not in _LEAN_AMPLITUDES
        ):
            raise InvalidContractError(
                f"state amplitude {index} is not supported by Lean"
            )

        expressions.append(_LEAN_AMPLITUDES[token])

    return expressions


def _format_state(
    tokens: Sequence[object],
    *,
    num_qubits: int,
) -> str:
    """Build an exact state function with Qiskit little-endian indexing."""

    amplitudes = _format_amplitudes(tokens)

    def build_tree(
        indices: list[int],
        bit: int,
    ) -> str:
        if bit < 0:
            return amplitudes[indices[0]]

        zero_indices = [
            index
            for index in indices
            if not index & (1 << bit)
        ]
        one_indices = [
            index
            for index in indices
            if index & (1 << bit)
        ]
        zero_branch = build_tree(zero_indices, bit - 1)
        one_branch = build_tree(one_indices, bit - 1)
        return (
            f"(if basis {bit} then "
            f"{one_branch} else {zero_branch})"
        )

    expression = build_tree(
        list(range(len(amplitudes))),
        num_qubits - 1,
    )
    return f"fun basis => {expression}"


def _format_gate(operation: Mapping[str, Any]) -> str:
    """Translate one validated IR operation to `Gate2` syntax."""

    gate = operation["gate"]
    targets = operation.get("targets", [])

    if gate == "I":
        return f".identity {targets[0]}"
    if gate in {"X", "Z", "H"}:
        return f".{gate.lower()} {targets[0]}"
    if gate == "CNOT":
        return (
            f".cnot {operation['controls'][0]} "
            f"{targets[0]} (by decide)"
        )
    if gate == "SWAP":
        return (
            f".swap {targets[0]} {targets[1]} "
            "(by decide)"
        )

    raise InvalidIrError(f"unsupported gate {gate!r}")


def generate_lean_module(
    ir: Mapping[str, Any],
    contract_data: Mapping[str, Any],
) -> GeneratedLeanModule:
    """Generate a checked proof obligation from shared circuit and contract data."""

    validate_ir(ir)

    # Report the boundary mismatch before parsing dimension-dependent fields.
    # This produces the most actionable diagnostic for pipeline users.
    if ir["qubits"] != contract_data.get("qubits"):
        raise InvalidContractError(
            f"circuit has {ir['qubits']} qubits but contract "
            f"requires {contract_data.get('qubits')}"
        )

    contract = contract_from_dict(contract_data)

    prefix = _lean_identifier(contract.name)
    circuit_name = f"generated{prefix}Circuit"
    input_name = f"generated{prefix}Input"
    target_name = f"generated{prefix}Target"
    theorem_name = f"generated{prefix}Correct"

    gates = ", ".join(
        _format_gate(operation)
        for operation in ir["operations"]
    )
    initial_state = _format_state(
        contract_data["initial_state"],
        num_qubits=contract.num_qubits,
    )
    target_state = _format_state(
        contract_data["target_state"],
        num_qubits=contract.num_qubits,
    )
    basis_cases = " <;> ".join(
        f"cases bit{index} : basis {index}"
        for index in range(contract.num_qubits)
    )
    case_names = ", ".join(
        f"bit{index}"
        for index in range(contract.num_qubits)
    )

    source = f"""import QuantumValidation.GeneralCircuit

/-!
Generated from circuit IR and contract schema version 0.1.
Regenerate this module instead of editing it by hand.
-/

namespace QuantumValidation
namespace General

def {circuit_name} : Circuit {contract.num_qubits} :=
  [{gates}]

noncomputable def {input_name} : State {contract.num_qubits} :=
  {initial_state}

noncomputable def {target_name} : State {contract.num_qubits} :=
  {target_state}

theorem {theorem_name} :
    denote {circuit_name} {input_name} = {target_name} := by
  classical
  funext basis
  {basis_cases} <;>
    simp [
      denote,
      {circuit_name},
      {input_name},
      {target_name},
      Gate.apply,
      setBit,
      flipBit,
      {case_names}
    ]

end General
end QuantumValidation
"""

    return GeneratedLeanModule(
        source=source,
        theorem_name=theorem_name,
    )


def write_lean_module(
    ir: Mapping[str, Any],
    contract_data: Mapping[str, Any],
    destination: str | Path,
) -> Path:
    """Write generated Lean source using deterministic UTF-8 output."""

    output_path = Path(destination)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    module = generate_lean_module(ir, contract_data)
    output_path.write_text(module.source, encoding="utf-8")
    return output_path
