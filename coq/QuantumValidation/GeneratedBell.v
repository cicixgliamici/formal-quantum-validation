From QuantumValidation Require Import Circuit.
Import QuantumValidationSQIR.

(*!
Generated from circuit IR and contract schema version 0.1.
Regenerate this module instead of editing it by hand.
*)

Definition bell_state_preparation_circuit : Circuit 2 :=
  GateH 0 :: GateCNOT 0 1 :: nil.

Definition bell_state_preparation_input : Vector 4 :=
  ∣0, 0⟩.

Definition bell_state_preparation_target : Vector 4 :=
  (/√2)%R .* ∣0, 0⟩ .+ (/√2)%R .* ∣1, 1⟩.

Theorem bell_state_preparation_circuit_well_formed :
  circuit_well_formed bell_state_preparation_circuit.
Proof.
  unfold bell_state_preparation_circuit, circuit_well_formed, gate_well_formed.
  repeat constructor; lia.
Qed.

Theorem bell_state_preparation_circuit_compile_well_typed :
  uc_well_typed (compile_circuit bell_state_preparation_circuit).
Proof.
  apply circuit_well_formed_compile_preservation.
  exact bell_state_preparation_circuit_well_formed.
Qed.

Theorem bell_state_preparation_correct :
  run bell_state_preparation_circuit × bell_state_preparation_input = bell_state_preparation_target.
Proof.
  unfold bell_state_preparation_circuit, bell_state_preparation_input, bell_state_preparation_target.
  solve_circuit.
Qed.
