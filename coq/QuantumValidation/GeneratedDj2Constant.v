From QuantumLib Require Import Complex Dirac.
From SQIR Require Import UnitarySem.
Open Scope ucom_scope.

(*!
Generated from circuit IR and contract schema version 0.1.
Regenerate this module instead of editing it by hand.
*)

Definition deutsch_jozsa_two_bit_constant_circuit : base_ucom 3 :=
  X 2 ; H 0 ; H 1 ; H 2 ; H 0 ; H 1.

Definition deutsch_jozsa_two_bit_constant_input : Vector 8 :=
  ∣0, 0, 0⟩.

Definition deutsch_jozsa_two_bit_constant_target : Vector 8 :=
  (/√2)%R .* ∣0, 0, 0⟩ .+ (- /√2)%R .* ∣0, 0, 1⟩.

Theorem deutsch_jozsa_two_bit_constant_correct :
  uc_eval deutsch_jozsa_two_bit_constant_circuit × deutsch_jozsa_two_bit_constant_input = deutsch_jozsa_two_bit_constant_target.
Proof.
  unfold deutsch_jozsa_two_bit_constant_circuit, deutsch_jozsa_two_bit_constant_input, deutsch_jozsa_two_bit_constant_target.
  simpl.
  Msimpl.
  autorewrite with eval_db.
  solve_matrix.
Qed.
