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

(* Keep source-level validity independent of SQIR so generated circuits expose
   exactly the bounds and distinctness guarantees supplied by checked IR. *)
Definition gate_well_formed {dim : nat} (gate : Gate dim) : Prop :=
  match gate with
  | GateI target
  | GateX target
  | GateZ target
  | GateH target => (target < dim)%nat
  | GateCNOT control target
  | GateSWAP control target =>
      (control < dim)%nat /\ (target < dim)%nat /\ control <> target
  end.

(* A positive dimension also makes the empty circuit's SKIP compilation valid. *)
Definition circuit_well_formed {dim : nat} (circuit : Circuit dim) : Prop :=
  (0 < dim)%nat /\ Forall gate_well_formed circuit.

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

Lemma compile_gate_well_typed {dim : nat} (gate : Gate dim) :
  gate_well_formed gate -> uc_well_typed (compile_gate gate).
Proof.
  destruct gate; cbn [gate_well_formed compile_gate]; intros valid.
  - apply uc_well_typed_ID. exact valid.
  - apply uc_well_typed_X. exact valid.
  - apply uc_well_typed_Rz. exact valid.
  - apply uc_well_typed_H. exact valid.
  - apply uc_well_typed_CNOT. exact valid.
  - destruct valid as [first_valid [second_valid distinct]].
    repeat apply WT_seq; apply uc_well_typed_CNOT; lia.
Qed.

Theorem circuit_well_formed_compile_preservation {dim : nat}
    (circuit : Circuit dim) :
  circuit_well_formed circuit -> uc_well_typed (compile_circuit circuit).
Proof.
  intros [positive_dim valid].
  induction circuit as [| gate remaining IH].
  - cbn [compile_circuit]. apply uc_well_typed_ID. exact positive_dim.
  - inversion valid as [| ? ? gate_valid remaining_valid]; subst.
    destruct remaining as [| next tail].
    + cbn [compile_circuit]. apply compile_gate_well_typed. exact gate_valid.
    + cbn [compile_circuit]. apply WT_seq.
      * apply compile_gate_well_typed. exact gate_valid.
      * apply IH. exact remaining_valid.
Qed.

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
