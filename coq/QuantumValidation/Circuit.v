From Coq Require Export List.
From QuantumLib Require Export Complex Quantum.
From SQIR Require Export UnitarySem.
Export ListNotations.

Module QuantumValidationSQIR.

(* Dimensions travel with circuits. Python's checked IR validates operand
   bounds and distinct two-qubit operands; these constructors do not certify
   bounds. SQIR-specific encodings belong only in compile_gate below. *)
Inductive Gate (dim : nat) : Type :=
| GateI (target : nat)
| GateX (target : nat)
| GateZ (target : nat)
| GateH (target : nat)
| GateCNOT (control target : nat)
| GateSWAP (first second : nat).

Arguments GateI {dim} _.
Arguments GateX {dim} _.
Arguments GateZ {dim} _.
Arguments GateH {dim} _.
Arguments GateCNOT {dim} _ _.
Arguments GateSWAP {dim} _ _.

Definition Circuit (dim : nat) := list (Gate dim).

Local Open Scope ucom_scope.

Definition compile_gate {dim : nat} (gate : Gate dim) : base_ucom dim :=
  match gate with
  | GateI target => ID target
  | GateX target => X target
  | GateZ target => Rz PI target
  | GateH target => H target
  | GateCNOT control target => CNOT control target
  | GateSWAP first second =>
      CNOT first second ; CNOT second first ; CNOT first second
  end.

(* List order is execution order. Avoid a trailing identity for nonempty lists.
   SKIP uses qubit zero, so the empty circuit requires a positive dimension,
   matching the nonempty-register restriction enforced by checked IR. *)
Fixpoint compile_circuit {dim : nat} (circuit : Circuit dim) : base_ucom dim :=
  match circuit with
  | [] => SKIP
  | [gate] => compile_gate gate
  | gate :: remaining => compile_gate gate ; compile_circuit remaining
  end.

Definition run {dim : nat} (circuit : Circuit dim) : Square (2 ^ dim) :=
  uc_eval (compile_circuit circuit).

(* SQIR tensors qubit zero on the left. The state serializer puts bit k of an
   IR amplitude index in ket position k. Bell/GHZ targets are reversal-invariant;
   asymmetric DJ and gate/basis cases test this convention. All tactics construct
   proof terms checked by Coq, including the final exact scalar algebra. *)
Ltac solve_circuit :=
  (* 1. Unfold semantic wrapper and inline circuit compiling. *)
  unfold run;
  cbn [compile_circuit compile_gate];
  simpl;
  (* 2. Evaluate SQIR program to a concrete Kronecker/matrix expression. *)
  Msimpl;
  autorewrite with eval_db;
  (* 3. Discharge positive register dimension side-condition (SKIP introduces 0 < dim). *)
  try lia;
  simpl;
  Msimpl;
  (* 4. Reduce matrix-vector product to entry-wise scalar equalities. *)
  solve_matrix;
  (* 5. Normalize real-to-complex embeddings and solve exact scalar field equations. *)
  autorewrite with RtoC_db;
  Csimpl;
  C_field.

End QuantumValidationSQIR.
