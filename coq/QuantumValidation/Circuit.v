From QuantumLib Require Import Complex Quantum.
From SQIR Require Import UnitarySem.
Open Scope ucom_scope.

(*!
Semantic bridge between Formal Quantum Validation IR and SQIR.

Supported IR Gate Mapping in SQIR (base_ucom dim):
  I q        -> ID q   (single-qubit identity uapp1 (U_R 0 0 0) q; 'skip' is not in base_ucom)
  X q        -> X q
  Z q        -> Rz PI q
  H q        -> H q
  CNOT c t   -> CNOT c t
  SWAP a b   -> CNOT a b ; CNOT b a ; CNOT a b
  (empty)    -> SKIP   (defined as ID 0 in SQIR)

Sequential gate composition in SQIR uses the infix operator ';' (at level 50).

SQIR Endianness and Reversal Invariance:
  In SQIR and QuantumLib, multi-qubit systems are tensored from qubit 0 to qubit n-1:
    v = q_0 ⊗ q_1 ⊗ ... ⊗ q_{n-1}
  In Dirac computational basis notation ∣b_0, b_1, ..., b_{n-1}⟩, the k-th entry
  corresponds to qubit k.

  NOTE ON REVERSAL INVARIANCE:
  We only noticed this endianness difference when introducing Deutsch-Jozsa,
  because Bell (|00⟩ + |11⟩)/√2 and GHZ(3) (|000⟩ + |111⟩)/√2 are completely
  symmetric under qubit reversal (reversal-invariant). In Deutsch-Jozsa, the ancilla
  (qubit 2) and query qubits (qubits 0, 1) break this symmetry, making the
  endianness convention essential.
*)

Module QuantumValidationSQIR.

Definition swap {dim : nat} (a b : nat) : base_ucom dim :=
  CNOT a b ; CNOT b a ; CNOT a b.

End QuantumValidationSQIR.
