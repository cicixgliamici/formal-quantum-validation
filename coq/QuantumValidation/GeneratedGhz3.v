From QuantumValidation Require Import Circuit.
Import QuantumValidationSQIR.

(*!
Generated from circuit IR and contract schema version 0.1.
Regenerate this module instead of editing it by hand.
*)

Definition ghz_three_qubit_preparation_circuit : Circuit 3 :=
  GateH 0 :: GateCNOT 0 1 :: GateCNOT 1 2 :: nil.

Definition ghz_three_qubit_preparation_input : Vector 8 :=
  ∣0, 0, 0⟩.

Definition ghz_three_qubit_preparation_target : Vector 8 :=
  (/√2)%R .* ∣0, 0, 0⟩ .+ (/√2)%R .* ∣1, 1, 1⟩.

Theorem ghz_three_qubit_preparation_correct :
  run ghz_three_qubit_preparation_circuit × ghz_three_qubit_preparation_input = ghz_three_qubit_preparation_target.
Proof.
  unfold ghz_three_qubit_preparation_circuit, ghz_three_qubit_preparation_input, ghz_three_qubit_preparation_target.
  solve_circuit.
Qed.
