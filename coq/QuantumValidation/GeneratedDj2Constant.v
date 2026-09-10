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

Theorem deutsch_jozsa_two_bit_constant_correct :
  run deutsch_jozsa_two_bit_constant_circuit × deutsch_jozsa_two_bit_constant_input = deutsch_jozsa_two_bit_constant_target.
Proof.
  unfold deutsch_jozsa_two_bit_constant_circuit, deutsch_jozsa_two_bit_constant_input, deutsch_jozsa_two_bit_constant_target.
  solve_circuit.
Qed.
