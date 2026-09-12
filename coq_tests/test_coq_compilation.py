"""Compile real obligations; missing Coq or SQIR is a failure, never a skip."""

import json
from pathlib import Path

import pytest

from fqv.backend.coq.generator import generate_coq_module
from fqv.frontend.qiskit.circuits import (
    build_dj2_balanced_circuit,
    build_dj2_constant_circuit,
)
from fqv.frontend.qiskit.extraction import circuit_to_ir

ROOT = Path(__file__).resolve().parents[1]


DJ_QISKIT_CASES = [
    ("constant", build_dj2_constant_circuit, "dj2_constant.contract.json"),
    ("balanced", build_dj2_balanced_circuit, "dj2_balanced.contract.json"),
]


@pytest.mark.parametrize("module", [
    "GeneratedBell", "GeneratedGhz3", "GeneratedDj2Constant",
    "GeneratedDj2Balanced",
])
def test_committed_module_compiles(module: str, tmp_path: Path, coq_compile) -> None:
    """Require each reviewed generated artifact to remain kernel-checkable.

    Drift tests answer whether generation is deterministic; this test answers
    the separate question of whether Coq accepts the committed proof term.
    """

    source = (ROOT / f"coq/QuantumValidation/{module}.v").read_text("utf-8")
    result = coq_compile(source, tmp_path / f"{module}.v")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("variant,builder,contract_file", DJ_QISKIT_CASES)
def test_dj_qiskit_to_coq_compiles(
    variant: str, builder, contract_file: str, tmp_path: Path, coq_compile,
) -> None:
    """Check the complete Qiskit -> checked IR -> Coq/SQIR proof path."""

    # Extract from the live Qiskit circuit so this test cannot pass merely
    # because a committed IR fixture agrees with a committed Coq artifact.
    ir = circuit_to_ir(builder())
    contract = json.loads(
        (ROOT / "src/fqv/data" / contract_file).read_text(encoding="utf-8")
    )
    generated = generate_coq_module(ir, contract)
    assert "_compile_well_typed" in generated.source
    result = coq_compile(generated.source, tmp_path / f"Dj2_{variant}.v")
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("example", ["dj2_constant", "dj2_balanced"])
def test_coq_rejects_mutated_dj_target(example: str, tmp_path: Path, coq_compile) -> None:
    """Show that a normalized but phase-wrong DJ target is not provable.

    The mutation changes an observable relative phase without breaking vector
    length or normalization. Compiling definitions separately ensures the final
    failure comes from the false equality rather than malformed generated Coq.
    """

    ir = json.loads((ROOT / f"examples/{example}_ir.json").read_text("utf-8"))
    contract = json.loads(
        (ROOT / f"src/fqv/data/{example}.contract.json").read_text("utf-8")
    )
    original = generate_coq_module(ir, contract).source
    # The positive control proves the fixture and toolchain are healthy before
    # the same circuit is paired with the deliberately wrong target.
    control = coq_compile(original, tmp_path / "Control.v")
    assert control.returncode == 0, control.stdout + control.stderr
    # Flip one branch, preserving normalization but changing the relative phase.
    index = contract["target_state"].index("minus_inv_sqrt_two")
    contract["target_state"][index] = "inv_sqrt_two"
    mutated = generate_coq_module(ir, contract).source
    assert mutated != original
    # First compile the mutated definitions alone: syntax/import failures must
    # never count as evidence that Coq rejected a false theorem.
    definitions = mutated.split("Theorem ", 1)[0]
    syntax = coq_compile(definitions, tmp_path / "Definitions.v")
    assert syntax.returncode == 0, syntax.stdout + syntax.stderr
    result = coq_compile(mutated, tmp_path / "Mutated.v")
    assert result.returncode != 0, "Coq accepted a false DJ target"
    assert "Error:" in result.stdout + result.stderr


def test_coq_rejects_ill_formed_circuit(tmp_path: Path, coq_compile) -> None:
    """Connect repeated CNOT operands to both source and SQIR rejection.

    The first lemma exercises `gate_well_formed`; the second checks the lowered
    SQIR program directly. Together they guard both sides of the preservation
    theorem instead of testing only the Python validator.
    """

    source = """From QuantumValidation Require Import Circuit.
Import QuantumValidationSQIR.

Example repeated_cnot_is_not_well_formed :
  ~ circuit_well_formed (GateCNOT 0 0 :: nil : Circuit 1).
Proof.
  (* Forall exposes the only gate's validity; its distinctness field is 0 <> 0. *)
  intros [_ gates_valid].
  inversion gates_valid as [| ? ? gate_valid]; subst.
  cbn [gate_well_formed] in gate_valid.
  destruct gate_valid as [_ [_ distinct]].
  exact (distinct eq_refl).
Qed.

Example repeated_cnot_compilation_is_not_well_typed :
  ~ uc_well_typed (compile_circuit (GateCNOT 0 0 :: nil : Circuit 1)).
Proof.
  (* SQIR's CNOT typing judgment carries the same distinct-wire requirement. *)
  cbn [compile_circuit compile_gate].
  intro typed.
  apply uc_well_typed_CNOT in typed as [_ [_ distinct]].
  exact (distinct eq_refl).
Qed.
"""
    result = coq_compile(source, tmp_path / "IllFormed.v")
    assert result.returncode == 0, result.stdout + result.stderr
