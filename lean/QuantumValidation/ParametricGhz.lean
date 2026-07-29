import QuantumValidation.GeneralUnitarity

/-!
Parametric correctness proof for preparation of the GHZ family.

The theorem covers every nonempty register. It uses a fan-out circuit with one
Hadamard on qubit zero followed by CNOTs from qubit zero to every other qubit.
This circuit is equivalent to the CNOT chain used by the fixed GHZ(3) example,
but its invariant is substantially clearer for an inductive proof.

Proof map:

1. `prefixBasis`, `ket`, and `ghzPrefix` describe the two basis branches that
   are present after each preparation step.
2. `hadamard_zero_starts_ghz` establishes the invariant for the first qubit.
3. The CNOT lemmas show how one fan-out gate acts on basis states and then on
   their scaled superposition.
4. `fanoutGate_advances` packages that local action as one invariant step.
5. `ghzFanout_correct` repeats the step by induction over all target qubits.
6. `ghz_correct` connects the initial Hadamard and the complete fan-out.

The longer pointwise proofs below deliberately expose basis assignments. This
keeps the argument close to the executable semantics in `GeneralCircuit`
instead of hiding the important bit transformations behind automation.
-/

namespace QuantumValidation
namespace General

/-- A basis assignment whose first `count` qubits are true. -/
def prefixBasis {n : Nat} (count : Nat) : Basis n :=
  fun qubit => decide (qubit.val < count)

/-- The computational-basis state concentrated at one basis assignment. -/
def ket {n : Nat} (assignment : Basis n) : State n :=
  fun basis => if basis = assignment then 1 else 0

/-- Pointwise addition of two states, kept explicit for readable statements. -/
def addState {n : Nat} (left right : State n) : State n :=
  fun basis => left basis + right basis

/-- Pointwise complex scaling of a state. -/
def scaleState {n : Nat} (scalar : ℂ) (state : State n) : State n :=
  fun basis => scalar * state basis

/-- The exact GHZ state on `n` qubits. -/
noncomputable def ghzState (n : Nat) : State n :=
  scaleState invSqrtTwo
    (addState (ket (prefixBasis 0)) (ket (prefixBasis n)))

/-- Intermediate superposition after entangling the first `count` qubits. -/
noncomputable def ghzPrefix {n : Nat} (count : Nat) : State n :=
  scaleState invSqrtTwo
    (addState (ket (prefixBasis 0)) (ket (prefixBasis count)))

/-- CNOT basis transformation, written independently for proof reuse. -/
private def cnotTransform {n : Nat} (control target : Fin n)
    (basis : Basis n) : Basis n :=
  if basis control then flipBit basis target else basis

/-- One fan-out CNOT from qubit zero to target `index`. -/
private def fanoutGate {n : Nat} (index : Nat)
    (positive : 0 < index) (inRange : index < n) : Gate n :=
  .cnot ⟨0, by omega⟩ ⟨index, inRange⟩ (by
    intro equal
    have := congrArg Fin.val equal
    simp at this
    omega)

/--
The first `count` fan-out gates for a fixed register.

The proof argument guarantees that targets `1, ..., count` are in range.
-/
def ghzFanout {n : Nat} :
    (count : Nat) → count + 1 ≤ n → Circuit n
  | 0, _ => []
  | count + 1, inRange =>
      ghzFanout count (by omega) ++
        [fanoutGate (count + 1) (by omega) (by omega)]

/-- The GHZ preparation circuit for every nonempty register size. -/
def ghzCircuit (n : Nat) (nonempty : 0 < n) : Circuit n :=
  [.h ⟨0, nonempty⟩] ++ ghzFanout (n - 1) (by omega)

/-- Hadamard creates the initial two-branch superposition on qubit zero. -/
private theorem hadamard_zero_starts_ghz {n : Nat} (nonempty : 0 < n) :
    Gate.apply (.h ⟨0, nonempty⟩) (ket (prefixBasis 0)) =
      ghzPrefix 1 := by
  classical
  -- State equality is proved pointwise. Splitting on the first bit matches
  -- the two branches selected by the Hadamard semantics.
  funext basis
  by_cases firstBit : basis ⟨0, nonempty⟩
  -- If the observed basis has bit zero set, only the |10...0> branch can
  -- contribute. The helper equivalences below make that statement usable by
  -- `simp` despite the state being expressed with `Function.update`.
  · have basisNotZero : basis ≠ prefixBasis 0 := by
      intro equal
      have := congrFun equal ⟨0, nonempty⟩
      simp [prefixBasis, firstBit] at this
    have updatedTrueNotZero :
        Function.update basis ⟨0, nonempty⟩ true ≠ prefixBasis 0 := by
      intro equal
      have := congrFun equal ⟨0, nonempty⟩
      simp [prefixBasis] at this
    have updatedFalse :
        Function.update basis ⟨0, nonempty⟩ false = prefixBasis 0 ↔
          basis = prefixBasis 1 := by
      constructor
      · intro equal
        funext qubit
        by_cases atZero : qubit = ⟨0, nonempty⟩
        · subst qubit
          simp [prefixBasis, firstBit]
        · have := congrFun equal qubit
          have nonzero : qubit.val ≠ 0 := by
            intro zero
            apply atZero
            apply Fin.ext
            simpa using zero
          simp [prefixBasis, Function.update, atZero, nonzero] at this ⊢
          exact this
      · intro equal
        subst basis
        funext qubit
        by_cases atZero : qubit = ⟨0, nonempty⟩
        · subst qubit
          simp [prefixBasis]
        · have nonzero : qubit.val ≠ 0 := by
            intro zero
            apply atZero
            apply Fin.ext
            simpa using zero
          simp [prefixBasis, Function.update, atZero, nonzero]
    simp [Gate.apply, ket, ghzPrefix, scaleState, addState, setBit,
      firstBit, basisNotZero, updatedTrueNotZero, updatedFalse]
  -- If bit zero is clear, the symmetric argument isolates the |00...0>
  -- branch. Keeping both cases explicit makes the amplitude accounting easy
  -- to audit.
  · have bitValue : basis ⟨0, nonempty⟩ = false :=
      Bool.eq_false_of_not_eq_true firstBit
    have basisNotOne : basis ≠ prefixBasis 1 := by
      intro equal
      have := congrFun equal ⟨0, nonempty⟩
      simp [prefixBasis, bitValue] at this
    have updatedTrueNotZero :
        Function.update basis ⟨0, nonempty⟩ true ≠ prefixBasis 0 := by
      intro equal
      have := congrFun equal ⟨0, nonempty⟩
      simp [prefixBasis] at this
    have updatedFalse :
        Function.update basis ⟨0, nonempty⟩ false = prefixBasis 0 ↔
          basis = prefixBasis 0 := by
      constructor
      · intro equal
        funext qubit
        by_cases atZero : qubit = ⟨0, nonempty⟩
        · subst qubit
          simp [prefixBasis, bitValue]
        · have := congrFun equal qubit
          simp [prefixBasis, Function.update, atZero] at this ⊢
          exact this
      · intro equal
        subst basis
        funext qubit
        simp [prefixBasis, Function.update]
    simp [Gate.apply, ket, ghzPrefix, scaleState, addState, setBit,
      firstBit, basisNotOne, updatedTrueNotZero, updatedFalse]

/-- The basis action of a valid CNOT is self-inverse. -/
private theorem cnotTransform_involutive {n : Nat}
    (control target : Fin n) (distinct : control ≠ target) :
    Function.Involutive (cnotTransform control target) := by
  intro basis
  by_cases controlBit : basis control <;>
    simp [cnotTransform, controlBit, flipBit, setBit, distinct]

/-- CNOT maps a basis ket to the ket at its transformed assignment. -/
private theorem cnot_apply_ket {n : Nat}
    (control target : Fin n) (distinct : control ≠ target)
    (assignment : Basis n) :
    Gate.apply (.cnot control target distinct) (ket assignment) =
      ket (cnotTransform control target assignment) := by
  classical
  funext basis
  simp only [Gate.apply, ket]
  -- A ket is selected by equality with its basis assignment. Since CNOT is
  -- involutive, testing the transformed input against `assignment` is the
  -- same as testing the input against the transformed assignment.
  have equivalent :
      cnotTransform control target basis = assignment ↔
        basis = cnotTransform control target assignment := by
    constructor
    · intro equal
      calc
        basis =
            cnotTransform control target
              (cnotTransform control target basis) :=
          (cnotTransform_involutive control target distinct basis).symm
        _ = cnotTransform control target assignment :=
          congrArg (cnotTransform control target) equal
    · intro equal
      calc
        cnotTransform control target basis =
            cnotTransform control target
              (cnotTransform control target assignment) :=
          congrArg (cnotTransform control target) equal
        _ = assignment :=
          cnotTransform_involutive control target distinct assignment
  -- The semantic definition of CNOT also splits on the control bit, so these
  -- cases reduce respectively to a bit flip and to the identity.
  by_cases controlBit : basis control
  · simp only [controlBit, if_true]
    have condition :
        flipBit basis target = assignment ↔
          basis = cnotTransform control target assignment := by
      simpa [cnotTransform, controlBit] using equivalent
    by_cases transformed : flipBit basis target = assignment
    · rw [if_pos transformed, if_pos (condition.mp transformed)]
    · rw [if_neg transformed, if_neg (fun equal => transformed (condition.mpr equal))]
  · simp only [controlBit]
    have condition :
        basis = assignment ↔
          basis = cnotTransform control target assignment := by
      simpa [cnotTransform, controlBit] using equivalent
    by_cases unchanged : basis = assignment
    · rw [if_pos unchanged, if_pos (condition.mp unchanged)]
      simp
    · rw [if_neg unchanged, if_neg (fun equal => unchanged (condition.mpr equal))]
      simp

/-- CNOT distributes through the scaled two-branch state representation. -/
private theorem cnot_apply_superposition {n : Nat}
    (control target : Fin n) (distinct : control ≠ target)
    (left right : State n) (scalar : ℂ) :
    Gate.apply (.cnot control target distinct)
        (scaleState scalar (addState left right)) =
      scaleState scalar
        (addState
          (Gate.apply (.cnot control target distinct) left)
          (Gate.apply (.cnot control target distinct) right)) := by
  funext basis
  by_cases controlBit : basis control <;>
    simp [Gate.apply, scaleState, addState, controlBit]

/-- Fan-out leaves the all-zero basis assignment unchanged. -/
private theorem cnotTransform_zero {n : Nat}
    (control target : Fin n) :
    cnotTransform control target (prefixBasis 0) = prefixBasis 0 := by
  funext qubit
  simp [cnotTransform, prefixBasis]

/-- The next fan-out CNOT extends the prefix of true qubits by one. -/
private theorem cnotTransform_prefix {n count : Nat}
    (positive : 0 < count) (inRange : count < n) :
    cnotTransform
        ⟨0, by omega⟩
        ⟨count, inRange⟩
        (prefixBasis count) =
      prefixBasis (count + 1) := by
  funext qubit
  -- At the target, CNOT changes false to true. Every other bit retains its
  -- previous membership in the true prefix.
  by_cases atTarget : qubit = ⟨count, inRange⟩
  · subst qubit
    simp [cnotTransform, prefixBasis, flipBit, setBit, positive]
  · have differentValue : qubit.val ≠ count := by
      intro equal
      apply atTarget
      apply Fin.ext
      exact equal
    simp [cnotTransform, prefixBasis, flipBit, setBit, positive, atTarget]
    omega

/-- One additional fan-out gate advances the GHZ prefix invariant. -/
private theorem fanoutGate_advances {n count : Nat}
    (positive : 0 < count) (inRange : count < n) :
    Gate.apply (fanoutGate count positive inRange) (ghzPrefix count) =
      ghzPrefix (count + 1) := by
  -- Distribute CNOT over the two GHZ branches: the zero branch is fixed,
  -- while the true prefix gains exactly the new target.
  unfold fanoutGate
  rw [ghzPrefix, cnot_apply_superposition]
  rw [cnot_apply_ket, cnot_apply_ket]
  rw [cnotTransform_zero, cnotTransform_prefix positive inRange]
  rfl

/-- Denotation respects concatenation of execution-ordered circuit lists. -/
private theorem denote_append {n : Nat} (first second : Circuit n)
    (state : State n) :
    denote (first ++ second) state = denote second (denote first state) := by
  simp [denote, List.foldl_append]

/-- The first `count` fan-out gates establish a prefix of `count + 1` ones. -/
private theorem ghzFanout_correct {n : Nat}
    (count : Nat) (inRange : count + 1 ≤ n) :
    denote (ghzFanout count inRange) (ghzPrefix 1) =
      ghzPrefix (count + 1) := by
  -- The induction follows the recursive circuit constructor exactly. The
  -- hypothesis handles the earlier targets; `fanoutGate_advances` handles
  -- the single gate appended for the successor case.
  induction count with
  | zero => rfl
  | succ previous inductionHypothesis =>
      rw [ghzFanout, denote_append]
      rw [inductionHypothesis (by omega)]
      simp only [denote, List.foldl_cons, List.foldl_nil]
      exact fanoutGate_advances (by omega) (by omega)

/--
The parametric GHZ preparation theorem.

For every nonempty register, the generated circuit maps the all-zero basis ket
to `(ket 0...0 + ket 1...1) / sqrt(2)`.
-/
theorem ghz_correct (n : Nat) (nonempty : 0 < n) :
    denote (ghzCircuit n nonempty) (ket (prefixBasis 0)) =
      ghzState n := by
  -- First expose sequential execution of H followed by the CNOT fan-out.
  rw [ghzCircuit, denote_append]
  change
    denote (ghzFanout (n - 1) _)
        (Gate.apply (.h ⟨0, nonempty⟩) (ket (prefixBasis 0))) =
      ghzState n
  -- The two main lemmas now connect directly: H establishes `ghzPrefix 1`,
  -- and fan-out grows it until every qubit belongs to the true branch.
  rw [hadamard_zero_starts_ghz]
  rw [ghzFanout_correct]
  have fullRegister : n - 1 + 1 = n := by omega
  rw [fullRegister]
  rfl

/-- GHZ(3) follows directly from the parametric family theorem. -/
theorem ghz_three_correct :
    denote (ghzCircuit 3 (by decide)) (ket (prefixBasis 0)) =
      ghzState 3 :=
  ghz_correct 3 (by decide)

end General
end QuantumValidation
