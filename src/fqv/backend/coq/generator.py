"""Translate shared IR and contracts into a Coq / SQIR proof obligation.

This module mirrors the Lean backend generator, translating validated circuit IR
and exact contract states into idiomatic Coq / SQIR definitions and theorems
using the circuit abstraction in QuantumValidation.Circuit and Dirac notation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from fqv.domain.amplitudes import AmplitudeToken
from fqv.domain.contract_parser import contract_from_dict
from fqv.domain.contract_validation import InvalidContractError
from fqv.ir.checked import CheckedOperation
from fqv.ir.validation import InvalidIrError, check_ir


class UnsupportedFormalizationError(ValueError):
    """Raised when valid shared input exceeds this backend's formal subset."""


_COQ_SCALARS: dict[AmplitudeToken, str | None] = {
    AmplitudeToken.ZERO: None,
    AmplitudeToken.ONE: "",
    AmplitudeToken.MINUS_ONE: "(- C1)%C .* ",
    AmplitudeToken.INV_SQRT_TWO: "(/√2)%R .* ",
    AmplitudeToken.MINUS_INV_SQRT_TWO: "(- /√2)%R .* ",
    AmplitudeToken.I: "Ci .* ",
    AmplitudeToken.MINUS_I: "(- Ci)%C .* ",
}


@dataclass(frozen=True)
class GeneratedCoqModule:
    """Deterministic Coq/SQIR artifact and its theorem name."""

    source: str
    theorem_name: str


def _coq_identifier(value: str) -> str:
    """Create a snake_case Coq identifier from an arbitrary contract name."""

    words = re.findall(r"[A-Za-z0-9]+", value)
    identifier = "_".join(word.lower() for word in words)

    if not identifier:
        raise UnsupportedFormalizationError(
            "contract name cannot produce a Coq identifier"
        )

    if identifier[0].isdigit():
        identifier = f"contract_{identifier}"

    return identifier


def _format_gate(operation: CheckedOperation) -> str:
    """Serialize public gate constructors; Circuit.v owns their SQIR meanings."""

    gate = operation.gate
    targets = operation.targets

    if gate in {"I", "X", "Z", "H"}:
        return f"Gate{gate} {targets[0]}"
    if gate == "CNOT":
        return f"GateCNOT {operation.controls[0]} {targets[0]}"
    if gate == "SWAP":
        return f"GateSWAP {targets[0]} {targets[1]}"

    raise InvalidIrError(f"unsupported gate {gate!r}")


def _format_state(
    tokens: Sequence[object],
    *,
    num_qubits: int,
) -> str:
    """Format exact amplitude tokens into QuantumLib Dirac vector notation.

    SQIR ENDIANNESS AND REVERSAL INVARIANCE:
    In SQIR and QuantumLib, the n-qubit tensor product is ordered from qubit 0 to
    qubit n-1 (left-to-right):
        v = q_0 ⊗ q_1 ⊗ ... ⊗ q_{n-1}
    Consequently, in Dirac notation ∣b_0, b_1, ..., b_{n-1}⟩, the k-th component
    corresponds directly to qubit k: b_k = (index >> k) & 1.

    Bell and GHZ targets are invariant under qubit reversal, so they cannot
    detect a reversed serializer. DJ assigns queries to qubits 0 and 1 and
    the ancilla to qubit 2; its asymmetric targets exercise this distinction.
    """

    terms: list[str] = []
    dim = 1 << num_qubits

    if len(tokens) != dim:
        raise InvalidContractError(
            f"expected {dim} amplitudes for {num_qubits} qubits, got {len(tokens)}"
        )

    for index, token in enumerate(tokens):
        if not isinstance(token, str):
            raise InvalidContractError(f"state amplitude {index} must be a string")

        try:
            amp_token = AmplitudeToken(token)
            scalar = _COQ_SCALARS[amp_token]
        except (KeyError, ValueError):
            raise InvalidContractError(
                f"state amplitude {token!r} is not supported by Coq backend"
            )

        if scalar is None:
            continue

        # In QuantumLib Dirac notation, ∣b_0, b_1, ..., b_{n-1}⟩ maps qubit k to position k.
        # Read low-order bits first to preserve the shared IR's little-endian meaning.
        bits = [(index >> k) & 1 for k in range(num_qubits)]
        basis_str = "∣" + ", ".join(str(b) for b in bits) + "⟩"
        terms.append(f"{scalar}{basis_str}")

    if not terms:
        return "Zero"

    if len(terms) == 1:
        return terms[0]

    return " .+ ".join(terms)


def generate_coq_module(
    ir: Mapping[str, Any],
    contract_data: Mapping[str, Any],
) -> GeneratedCoqModule:
    """Generate a kernel-checkable SQIR obligation from IR and contract."""

    checked_ir = check_ir(ir)

    if not isinstance(contract_data, dict):
        raise InvalidContractError("contract must be a JSON object")
    if checked_ir.num_qubits != contract_data.get("qubits"):
        raise InvalidContractError(
            f"circuit has {checked_ir.num_qubits} qubits but contract "
            f"requires {contract_data.get('qubits')}"
        )

    contract = contract_from_dict(contract_data)

    prefix = _coq_identifier(contract.name)
    circuit_name = f"{prefix}_circuit"
    input_name = f"{prefix}_input"
    target_name = f"{prefix}_target"
    theorem_name = f"{prefix}_correct"

    # Cons notation avoids SQIR's competing semicolon notation for composition.
    gates_str = " :: ".join([*(_format_gate(op) for op in checked_ir.operations), "nil"])

    input_expr = _format_state(
        contract_data["initial_state"],
        num_qubits=contract.num_qubits,
    )
    target_expr = _format_state(
        contract_data["target_state"],
        num_qubits=contract.num_qubits,
    )

    vector_dim = 1 << contract.num_qubits

    source = f"""From QuantumValidation Require Import Circuit.
Import QuantumValidationSQIR.

(*!
Generated from circuit IR and contract schema version 0.1.
Regenerate this module instead of editing it by hand.
*)

Definition {circuit_name} : Circuit {contract.num_qubits} :=
  {gates_str}.

Definition {input_name} : Vector {vector_dim} :=
  {input_expr}.

Definition {target_name} : Vector {vector_dim} :=
  {target_expr}.

Theorem {circuit_name}_well_formed :
  circuit_well_formed {circuit_name}.
Proof.
  unfold {circuit_name}, circuit_well_formed, gate_well_formed.
  repeat constructor; lia.
Qed.

Theorem {circuit_name}_compile_well_typed :
  uc_well_typed (compile_circuit {circuit_name}).
Proof.
  apply circuit_well_formed_compile_preservation.
  exact {circuit_name}_well_formed.
Qed.

Theorem {theorem_name} :
  run {circuit_name} × {input_name} = {target_name}.
Proof.
  unfold {circuit_name}, {input_name}, {target_name}.
  solve_circuit.
Qed.
"""

    return GeneratedCoqModule(
        source=source,
        theorem_name=theorem_name,
    )


def write_coq_module(
    ir: Mapping[str, Any],
    contract_data: Mapping[str, Any],
    destination: str | Path,
) -> Path:
    """Write generated Coq source using deterministic UTF-8 output."""

    output_path = Path(destination)
    module = generate_coq_module(ir, contract_data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(module.source, encoding="utf-8", newline="\n")
    return output_path
