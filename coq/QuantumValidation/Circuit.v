From QuantumLib Require Import Complex Dirac.
From SQIR Require Import UnitarySem.
Open Scope ucom_scope.

(*!
Semantic bridge between Formal Quantum Validation IR and SQIR.

Supported IR Gate Mapping:
  I q        -> skip
  X q        -> X q
  Z q        -> Rz PI q  (or H q ;; X q ;; H q)
  H q        -> H q
  CNOT c t   -> CNOT c t
  SWAP a b   -> CNOT a b ;; CNOT b a ;; CNOT a b

Quantum states are represented as column vectors in QuantumLib (Vector (2^dim))
using Dirac computational basis notation: ∣b_{n-1}, ..., b_0⟩.
*)

Module QuantumValidationSQIR.

Definition swap {dim : nat} (a b : nat) : base_ucom dim :=
  CNOT a b ;; CNOT b a ;; CNOT a b.

End QuantumValidationSQIR.
