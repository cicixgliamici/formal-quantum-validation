from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from fqv.domain.contract_parser import contract_from_dict
from fqv.domain.contract_validation import InvalidContractError
from fqv.ir.validation import InvalidIrError, check_ir


class UnsupportedFormalizationError(ValueError):
    """Raised when valid shared input exceeds this backend's formal subset.

    The distinction from `InvalidIrError` matters: an input may be valid for
    another backend while still lacking an exact Lean translation.
    """


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
    """Deterministic Lean artifact and its externally relevant theorem name.

    Returning source as data keeps generation testable without writing files.
    File output is a separate responsibility handled by `write_lean_module`.
    """

    source: str
    theorem_name: str


def _lean_identifier(value: str) -> str:
    """Create a readable and deterministic Lean identifier.

    Contract names are external data and may contain spaces or punctuation.
    Sanitizing them in one place prevents naming rules from drifting between
    generated definitions and theorem statements.
    """

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
        """Recursively emit one Boolean decision tree over basis bits."""

        if bit < 0:
            return amplitudes[indices[0]]

        # The tree tests the most significant displayed bit first but indexes
        # amplitudes using Qiskit's little-endian integer convention.
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
    """Translate one validated IR operation to general Lean gate syntax.

    Distinct CNOT and SWAP operands were checked at the Python boundary. Lean
    still receives `(by decide)` so its own type checker independently confirms
    that the concrete generated operands differ.
    """

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
    """Generate a kernel-checkable obligation from shared source artifacts.

    Generation itself remains trusted Python code. Assurance comes from Lean
    checking the emitted theorem and from CI detecting drift between committed
    inputs and generated source.
    """

    check_ir(ir)

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

    # Circuit order is copied directly. Reordering valid gates would be a
    # semantic generator defect, so regression tests compare complete source.
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
    # Fixed-size generated examples use exhaustive Boolean case splitting.
    # Parametric families such as GHZ(n) are proved separately by induction.
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
