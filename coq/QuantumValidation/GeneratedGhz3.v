From QuantumLib Require Import Complex Dirac.
From SQIR Require Import UnitarySem.
Open Scope ucom_scope.

(*!
Generated from circuit IR and contract schema version 0.1.
Regenerate this module instead of editing it by hand.
*)

Definition ghz_three_qubit_preparation_circuit : base_ucom 3 :=
  H 0 ; CNOT 0 1 ; CNOT 1 2.

Definition ghz_three_qubit_preparation_input : Vector 8 :=
  ∣0, 0, 0⟩.

Definition ghz_three_qubit_preparation_target : Vector 8 :=
  (/√2)%R .* ∣0, 0, 0⟩ .+ (/√2)%R .* ∣1, 1, 1⟩.

Theorem ghz_three_qubit_preparation_correct :
  uc_eval ghz_three_qubit_preparation_circuit × ghz_three_qubit_preparation_input = ghz_three_qubit_preparation_target.
Proof.
  unfold ghz_three_qubit_preparation_circuit, ghz_three_qubit_preparation_input, ghz_three_qubit_preparation_target.
  simpl.
  Msimpl.
  autorewrite with eval_db.
  solve_matrix.
Qed.
