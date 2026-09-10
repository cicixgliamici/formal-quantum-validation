"""Translate shared IR and contracts into a Coq / SQIR proof obligation.

This module mirrors the Lean backend generator, translating validated circuit IR
and exact contract states into idiomatic Coq / SQIR definitions and theorems
using QuantumLib's unitary semantics (`uc_eval`) and Dirac notation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from fqv.domain.contract_parser import contract_from_dict
from fqv.domain.contract_validation import InvalidContractError
from fqv.ir.checked import CheckedOperation
from fqv.ir.validation import InvalidIrError, check_ir


class UnsupportedFormalizationError(ValueError):
    """Raised when valid shared input exceeds this backend's formal subset."""


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
    """Translate one validated IR operation to SQIR base_ucom syntax.

    In SQIR:
    - Identity on qubit q is `ID q` (single-qubit identity on qubit q, defined as
      `uapp1 (U_R 0 0 0) q`). `skip` is not an identity constructor for base_ucom.
    - Sequential composition uses the `;` infix operator from `ucom_scope`.
    - SWAP is decomposed into three CNOT gates: `CNOT t0 t1 ; CNOT t1 t0 ; CNOT t0 t1`.
    """

    gate = operation.gate
    targets = operation.targets

    if gate == "I":
        return f"ID {targets[0]}"
    if gate == "X":
        return f"X {targets[0]}"
    if gate == "Z":
        return f"Rz PI {targets[0]}"
    if gate == "H":
        return f"H {targets[0]}"
    if gate == "CNOT":
        return f"CNOT {operation.controls[0]} {targets[0]}"
    if gate == "SWAP":
        t0, t1 = targets[0], targets[1]
        return f"CNOT {t0} {t1} ; CNOT {t1} {t0} ; CNOT {t0} {t1}"

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

    NOTE ON REVERSAL INVARIANCE:
    We only noticed this endianness difference when introducing Deutsch-Jozsa,
    because Bell (|00⟩ + |11⟩)/√2 and GHZ(3) (|000⟩ + |111⟩)/√2 are completely
    symmetric under qubit reversal (reversal-invariant). In Deutsch-Jozsa, where
    the ancilla is qubit 2 and query qubits are 0 and 1, this reversal asymmetry
    makes the endianness convention essential.
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

        if token == "zero":
            continue

        # In QuantumLib Dirac notation, ∣b_0, b_1, ..., b_{n-1}⟩ maps qubit k to position k.
        # Bell and GHZ are invariant under bit reversal, so only Deutsch-Jozsa revealed this.
        bits = [(index >> k) & 1 for k in range(num_qubits)]
        basis_str = "∣" + ", ".join(str(b) for b in bits) + "⟩"

        if token == "one":
            term = basis_str
        elif token == "minus_one":
            term = f"(- C1)%R .* {basis_str}"
        elif token == "inv_sqrt_two":
            term = f"(/√2)%R .* {basis_str}"
        elif token == "minus_inv_sqrt_two":
            term = f"(- /√2)%R .* {basis_str}"
        elif token == "i":
            term = f"Ci .* {basis_str}"
        elif token == "minus_i":
            term = f"(- Ci)%R .* {basis_str}"
        else:
            raise InvalidContractError(
                f"state amplitude {token!r} is not supported by Coq backend"
            )

        terms.append(term)

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

    if checked_ir.operations:
        gates_str = " ; ".join(_format_gate(op) for op in checked_ir.operations)
    else:
        gates_str = "SKIP"


    input_expr = _format_state(
        contract_data["initial_state"],
        num_qubits=contract.num_qubits,
    )
    target_expr = _format_state(
        contract_data["target_state"],
        num_qubits=contract.num_qubits,
    )

    vector_dim = 1 << contract.num_qubits

    # QuantumLib 1.7 exposes Dirac notation through Quantum, not a Dirac module.
    source = f"""From QuantumLib Require Import Complex Quantum.
From SQIR Require Import UnitarySem.
Open Scope ucom_scope.

(*!
Generated from circuit IR and contract schema version 0.1.
Regenerate this module instead of editing it by hand.
*)

Definition {circuit_name} : base_ucom {contract.num_qubits} :=
  {gates_str}.

Definition {input_name} : Vector {vector_dim} :=
  {input_expr}.

Definition {target_name} : Vector {vector_dim} :=
  {target_expr}.

Theorem {theorem_name} :
  uc_eval {circuit_name} × {input_name} = {target_name}.
Proof.
  unfold {circuit_name}, {input_name}, {target_name}.
  simpl.
  Msimpl.
  autorewrite with eval_db.
  solve_matrix.
  (* Matrix reduction leaves exact scalar identities involving sqrt(2). *)
  all: autorewrite with RtoC_db; Csimpl; C_field.
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
