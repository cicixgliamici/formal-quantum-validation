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

Theorem ghz_three_qubit_preparation_circuit_well_formed :
  circuit_well_formed ghz_three_qubit_preparation_circuit.
Proof.
  unfold ghz_three_qubit_preparation_circuit, circuit_well_formed, gate_well_formed.
  repeat constructor; lia.
Qed.

Theorem ghz_three_qubit_preparation_circuit_compile_well_typed :
  uc_well_typed (compile_circuit ghz_three_qubit_preparation_circuit).
Proof.
  apply circuit_well_formed_compile_preservation.
  exact ghz_three_qubit_preparation_circuit_well_formed.
Qed.

Theorem ghz_three_qubit_preparation_correct :
  run ghz_three_qubit_preparation_circuit × ghz_three_qubit_preparation_input = ghz_three_qubit_preparation_target.
Proof.
  unfold ghz_three_qubit_preparation_circuit, ghz_three_qubit_preparation_input, ghz_three_qubit_preparation_target.
  solve_circuit.
Qed.
