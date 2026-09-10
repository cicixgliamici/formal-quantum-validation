From QuantumValidation Require Import Circuit.
Import QuantumValidationSQIR.

(*!
Generated from circuit IR and contract schema version 0.1.
Regenerate this module instead of editing it by hand.
*)

Definition deutsch_jozsa_two_bit_constant_circuit : Circuit 3 :=
  GateX 2 :: GateH 0 :: GateH 1 :: GateH 2 :: GateH 0 :: GateH 1 :: nil.

Definition deutsch_jozsa_two_bit_constant_input : Vector 8 :=
  ∣0, 0, 0⟩.

Definition deutsch_jozsa_two_bit_constant_target : Vector 8 :=
  (/√2)%R .* ∣0, 0, 0⟩ .+ (- /√2)%R .* ∣0, 0, 1⟩.

Theorem deutsch_jozsa_two_bit_constant_circuit_well_formed :
  circuit_well_formed deutsch_jozsa_two_bit_constant_circuit.
Proof.
  unfold deutsch_jozsa_two_bit_constant_circuit, circuit_well_formed, gate_well_formed.
  repeat constructor; lia.
Qed.

Theorem deutsch_jozsa_two_bit_constant_circuit_compile_well_typed :
  uc_well_typed (compile_circuit deutsch_jozsa_two_bit_constant_circuit).
Proof.
  apply circuit_well_formed_compile_preservation.
  exact deutsch_jozsa_two_bit_constant_circuit_well_formed.
Qed.

Theorem deutsch_jozsa_two_bit_constant_correct :
  run deutsch_jozsa_two_bit_constant_circuit × deutsch_jozsa_two_bit_constant_input = deutsch_jozsa_two_bit_constant_target.
Proof.
  unfold deutsch_jozsa_two_bit_constant_circuit, deutsch_jozsa_two_bit_constant_input, deutsch_jozsa_two_bit_constant_target.
  solve_circuit.
Qed.
