From QuantumLib Require Import Complex Quantum.
From SQIR Require Import UnitarySem.
Open Scope ucom_scope.

(*!
Generated from circuit IR and contract schema version 0.1.
Regenerate this module instead of editing it by hand.
*)

Definition bell_state_preparation_circuit : base_ucom 2 :=
  H 0 ; CNOT 0 1.

Definition bell_state_preparation_input : Vector 4 :=
  ∣0, 0⟩.

Definition bell_state_preparation_target : Vector 4 :=
  (/√2)%R .* ∣0, 0⟩ .+ (/√2)%R .* ∣1, 1⟩.

Theorem bell_state_preparation_correct :
  uc_eval bell_state_preparation_circuit × bell_state_preparation_input = bell_state_preparation_target.
Proof.
  unfold bell_state_preparation_circuit, bell_state_preparation_input, bell_state_preparation_target.
  simpl.
  Msimpl.
  autorewrite with eval_db.
  solve_matrix.
  (* Matrix reduction leaves exact scalar identities involving sqrt(2). *)
  all: autorewrite with RtoC_db; Csimpl; C_field.
Qed.
