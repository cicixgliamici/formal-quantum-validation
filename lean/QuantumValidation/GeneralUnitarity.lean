import QuantumValidation.GeneralProperties
import Mathlib.Algebra.BigOperators.Group.Finset.Basic

/-!
Unitarity and normalization preservation for the general finite semantics.

The definitions use the finite computational basis directly. This keeps the
proof boundary close to the executable gate semantics and avoids introducing
an independent matrix representation that could disagree with `Gate.apply`.
-/

namespace QuantumValidation
namespace General

open Complex
open scoped BigOperators

/-- The finite-dimensional complex inner product of two pure states. -/
noncomputable def inner {n : Nat} (left right : State n) : ℂ :=
  ∑ basis, star (left basis) * right basis

/--
The squared norm is the real part of the self-inner-product.

Each summand is `conj amplitude * amplitude`, so this is the standard total
computational-basis probability weight.
-/
noncomputable def normSquared {n : Nat} (state : State n) : ℝ :=
  (inner state state).re

/-- A state is normalized when its total computational-basis weight is one. -/
def IsNormalized {n : Nat} (state : State n) : Prop :=
  normSquared state = 1

/--
A semantic gate is unitary when it preserves the complex inner product.

This definition is equivalent to the usual matrix equation `U†U = I` in the
finite state space, while referring directly to the project's gate semantics.
-/
def IsUnitary {n : Nat} (gate : Gate n) : Prop :=
  ∀ left right,
    inner (gate.apply left) (gate.apply right) = inner left right

/-- Inner-product preservation implies preservation of the squared norm. -/
theorem normSquared_eq_inner_re {n : Nat} (state : State n) :
    normSquared state = (inner state state).re := by
  rfl

/-- Every unitary semantic gate preserves the squared norm. -/
theorem IsUnitary.preserves_normSquared {n : Nat} {gate : Gate n}
    (unitary : IsUnitary gate) (state : State n) :
    normSquared (gate.apply state) = normSquared state := by
  rw [normSquared_eq_inner_re, normSquared_eq_inner_re, unitary]

/-- Every unitary semantic gate preserves state normalization. -/
theorem IsUnitary.preserves_normalization {n : Nat} {gate : Gate n}
    (unitary : IsUnitary gate) {state : State n}
    (normalized : IsNormalized state) :
    IsNormalized (gate.apply state) := by
  rw [IsNormalized, unitary.preserves_normSquared, normalized]

/--
Pairwise equality over an involution implies equality of the complete sums.

This is the reusable bookkeeping step for Hadamard: every basis element is
paired with the basis element obtained by flipping the target bit.
-/
private theorem sum_eq_of_involution_pairs {α : Type*} [Fintype α]
    (permutation : Equiv.Perm α)
    (left right : α → ℂ)
    (pairsEqual :
      ∀ value,
        left value + left (permutation value) =
          right value + right (permutation value)) :
    ∑ value, left value = ∑ value, right value := by
  have leftInvariant :
      (∑ value, left (permutation value)) = ∑ value, left value := by
    exact Fintype.sum_equiv permutation
      (fun value => left (permutation value)) left (fun value => rfl)
  have rightInvariant :
      (∑ value, right (permutation value)) = ∑ value, right value := by
    exact Fintype.sum_equiv permutation
      (fun value => right (permutation value)) right (fun value => rfl)
  have doubled :
      2 * (∑ value, left value) = 2 * (∑ value, right value) := by
    calc
      2 * (∑ value, left value) =
          (∑ value, left value) + ∑ value, left (permutation value) := by
            rw [leftInvariant]
            ring
      _ = ∑ value, (left value + left (permutation value)) := by
            rw [Finset.sum_add_distrib]
      _ = ∑ value, (right value + right (permutation value)) := by
            apply Finset.sum_congr rfl
            intro value _
            exact pairsEqual value
      _ = (∑ value, right value) + ∑ value, right (permutation value) := by
            rw [Finset.sum_add_distrib]
      _ = 2 * (∑ value, right value) := by
            rw [rightInvariant]
            ring
  exact mul_left_cancel₀ (by norm_num : (2 : ℂ) ≠ 0) doubled

/-- Flipping one selected bit is an involution on the computational basis. -/
private theorem flipBit_involutive {n : Nat} (target : Fin n) :
    Function.Involutive (fun basis : Basis n => flipBit basis target) := by
  intro basis
  funext position
  by_cases same : position = target
  · subst position
    simp [flipBit, setBit]
  · simp [flipBit, setBit, same]

/-- Writing the bit already stored at a position leaves a basis unchanged. -/
private theorem setBit_current {n : Nat} (basis : Basis n) (target : Fin n) :
    setBit basis target (basis target) = basis := by
  funext position
  by_cases same : position = target
  · subst position
    simp [setBit]
  · simp [setBit, same]

/-- The basis permutation induced by `X` at one target. -/
private def flipBitPermutation {n : Nat} (target : Fin n) :
    Equiv.Perm (Basis n) :=
  (flipBit_involutive target).toPerm

/-- Identity is unitary for every valid target and register size. -/
theorem identity_unitary {n : Nat} (target : Fin n) :
    IsUnitary (.identity target) := by
  intro left right
  rfl

/-- Pauli-X is unitary for every valid target and register size. -/
theorem x_unitary {n : Nat} (target : Fin n) :
    IsUnitary (.x target) := by
  intro left right
  unfold inner
  simp only [Gate.apply]
  exact Fintype.sum_equiv
    (flipBitPermutation target)
    (fun basis =>
      star (left (flipBit basis target)) *
        right (flipBit basis target))
    (fun basis =>
      star (left basis) * right basis)
    (fun basis => rfl)

/-- Pauli-Z is unitary for every valid target and register size. -/
theorem z_unitary {n : Nat} (target : Fin n) :
    IsUnitary (.z target) := by
  intro left right
  unfold inner
  apply Finset.sum_congr rfl
  intro basis _
  by_cases bit : basis target <;>
    simp [Gate.apply, bit]

/-- The Hadamard scaling factor has squared magnitude `1 / 2`. -/
private theorem invSqrtTwo_star_mul :
    star invSqrtTwo * invSqrtTwo = (2 : ℂ)⁻¹ := by
  calc
    _ = (Complex.normSq invSqrtTwo : ℂ) :=
      (Complex.normSq_eq_conj_mul_self (z := invSqrtTwo)).symm
    _ = _ := by
      simp only [invSqrtTwo, Complex.normSq_inv, Complex.normSq_ofReal]
      rw [show Real.sqrt 2 * Real.sqrt 2 = (2 : ℝ) by
        exact Real.mul_self_sqrt (by norm_num)]
      norm_num

/--
The two Hadamard output amplitudes preserve the inner-product contribution of
their two input amplitudes.
-/
private theorem hadamard_pair_identity
    (leftZero leftOne rightZero rightOne : ℂ) :
    star ((leftZero + leftOne) * invSqrtTwo) *
          ((rightZero + rightOne) * invSqrtTwo) +
        star ((leftZero - leftOne) * invSqrtTwo) *
          ((rightZero - rightOne) * invSqrtTwo) =
      star leftZero * rightZero + star leftOne * rightOne := by
  rw [star_mul', star_mul', star_add, star_sub]
  calc
    _ = (star invSqrtTwo * invSqrtTwo) *
        ((star leftZero + star leftOne) * (rightZero + rightOne) +
          (star leftZero - star leftOne) * (rightZero - rightOne)) := by
      ring
    _ = _ := by
      rw [invSqrtTwo_star_mul]
      norm_num
      ring

/-- Expanded form used after Lean unfolds `star` through Hadamard outputs. -/
private theorem hadamard_pair_identity_expanded
    (leftZero leftOne rightZero rightOne : ℂ) :
    ((starRingEnd ℂ) leftZero + (starRingEnd ℂ) leftOne) *
          (starRingEnd ℂ) invSqrtTwo *
          ((rightZero + rightOne) * invSqrtTwo) +
        ((starRingEnd ℂ) leftZero - (starRingEnd ℂ) leftOne) *
          (starRingEnd ℂ) invSqrtTwo *
          ((rightZero - rightOne) * invSqrtTwo) =
      (starRingEnd ℂ) leftZero * rightZero +
        (starRingEnd ℂ) leftOne * rightOne := by
  calc
    _ = ((starRingEnd ℂ) invSqrtTwo * invSqrtTwo) *
        (((starRingEnd ℂ) leftZero + (starRingEnd ℂ) leftOne) *
            (rightZero + rightOne) +
          ((starRingEnd ℂ) leftZero - (starRingEnd ℂ) leftOne) *
            (rightZero - rightOne)) := by
      ring
    _ = _ := by
      change (star invSqrtTwo * invSqrtTwo) * _ = _
      rw [invSqrtTwo_star_mul]
      norm_num
      ring

/-- Hadamard is unitary for every valid target and register size. -/
theorem h_unitary {n : Nat} (target : Fin n) :
    IsUnitary (.h target) := by
  intro left right
  unfold inner
  apply sum_eq_of_involution_pairs (flipBitPermutation target)
  intro basis
  change
    (star ((Gate.h target).apply left basis) *
          (Gate.h target).apply right basis) +
        (star ((Gate.h target).apply left (flipBit basis target)) *
          (Gate.h target).apply right (flipBit basis target)) =
      (star (left basis) * right basis) +
        star (left (flipBit basis target)) *
          right (flipBit basis target)
  by_cases bit : basis target
  · have current : setBit basis target true = basis := by
      rw [← bit]
      apply setBit_current
    rw [← current]
    simp only [Gate.apply]
    simp [flipBit, setBit]
    simpa only [setBit, add_comm] using
      hadamard_pair_identity_expanded
      (left (setBit basis target false))
      (left (setBit basis target true))
      (right (setBit basis target false))
      (right (setBit basis target true))
  · have bitValue : basis target = false :=
      Bool.eq_false_of_not_eq_true bit
    have current : setBit basis target false = basis := by
      rw [← bitValue]
      apply setBit_current
    rw [← current]
    simp only [Gate.apply]
    simp [flipBit, setBit]
    simpa only [setBit] using
      hadamard_pair_identity_expanded
      (left (setBit basis target false))
      (left (setBit basis target true))
      (right (setBit basis target false))
      (right (setBit basis target true))

/-- The basis transformation read by a CNOT semantic gate. -/
private def cnotBasis {n : Nat} (control target : Fin n)
    (basis : Basis n) : Basis n :=
  if basis control then flipBit basis target else basis

/-- A valid CNOT basis transformation is self-inverse. -/
private theorem cnotBasis_involutive {n : Nat}
    (control target : Fin n) (distinct : control ≠ target) :
    Function.Involutive (cnotBasis control target) := by
  intro basis
  by_cases bit : basis control <;>
    simp [cnotBasis, bit, flipBit, setBit, distinct]

/-- The permutation of basis assignments induced by CNOT. -/
private def cnotPermutation {n : Nat}
    (control target : Fin n) (distinct : control ≠ target) :
    Equiv.Perm (Basis n) :=
  (cnotBasis_involutive control target distinct).toPerm

/-- CNOT is unitary for every pair of distinct valid operands. -/
theorem cnot_unitary {n : Nat}
    (control target : Fin n) (distinct : control ≠ target) :
    IsUnitary (.cnot control target distinct) := by
  intro left right
  unfold inner
  calc
    _ = ∑ basis,
        star (left (cnotBasis control target basis)) *
          right (cnotBasis control target basis) := by
      apply Finset.sum_congr rfl
      intro basis _
      by_cases bit : basis control <;>
        simp [Gate.apply, cnotBasis, bit]
    _ = _ := Fintype.sum_equiv
      (cnotPermutation control target distinct)
      (fun basis =>
        star (left (cnotBasis control target basis)) *
          right (cnotBasis control target basis))
      (fun basis => star (left basis) * right basis)
      (fun basis => rfl)

/-- The basis transformation read by a SWAP semantic gate. -/
private def swapBasis {n : Nat} (left right : Fin n)
    (basis : Basis n) : Basis n :=
  setBit
    (setBit basis left (basis right))
    right
    (basis left)

/-- A valid SWAP basis transformation is self-inverse. -/
private theorem swapBasis_involutive {n : Nat}
    (left right : Fin n) (distinct : left ≠ right) :
    Function.Involutive (swapBasis left right) := by
  intro basis
  funext position
  by_cases atLeft : position = left
  · subst position
    simp [swapBasis, setBit, distinct]
  · by_cases atRight : position = right
    · subst position
      simp [swapBasis, setBit, distinct]
    · simp [swapBasis, setBit, atLeft, atRight]

/-- The permutation of basis assignments induced by SWAP. -/
private def swapPermutation {n : Nat}
    (left right : Fin n) (distinct : left ≠ right) :
    Equiv.Perm (Basis n) :=
  (swapBasis_involutive left right distinct).toPerm

/-- SWAP is unitary for every pair of distinct valid operands. -/
theorem swap_unitary {n : Nat}
    (left right : Fin n) (distinct : left ≠ right) :
    IsUnitary (.swap left right distinct) := by
  intro first second
  unfold inner
  simp only [Gate.apply]
  exact Fintype.sum_equiv
    (swapPermutation left right distinct)
    (fun basis =>
      star (first (swapBasis left right basis)) *
        second (swapBasis left right basis))
    (fun basis => star (first basis) * second basis)
    (fun basis => rfl)

/-- Every gate admitted by the formal circuit syntax is unitary. -/
theorem gate_unitary {n : Nat} (gate : Gate n) :
    IsUnitary gate := by
  cases gate with
  | identity target => exact identity_unitary target
  | x target => exact x_unitary target
  | z target => exact z_unitary target
  | h target => exact h_unitary target
  | cnot control target distinct =>
      exact cnot_unitary control target distinct
  | swap left right distinct =>
      exact swap_unitary left right distinct

/-- Every supported circuit preserves the complex inner product. -/
theorem denote_preserves_inner {n : Nat} (circuit : Circuit n)
    (left right : State n) :
    inner (denote circuit left) (denote circuit right) =
      inner left right := by
  induction circuit generalizing left right with
  | nil => rfl
  | cons gate remaining inductionHypothesis =>
      simp only [denote, List.foldl_cons]
      calc
        inner
            (List.foldl (fun state next => next.apply state)
              (gate.apply left) remaining)
            (List.foldl (fun state next => next.apply state)
              (gate.apply right) remaining) =
            inner (gate.apply left) (gate.apply right) :=
          inductionHypothesis (gate.apply left) (gate.apply right)
        _ = inner left right := gate_unitary gate left right

/-- Every supported circuit preserves the squared norm of every state. -/
theorem denote_preserves_normSquared {n : Nat} (circuit : Circuit n)
    (state : State n) :
    normSquared (denote circuit state) = normSquared state := by
  rw [normSquared, normSquared, denote_preserves_inner]

/-- Every supported circuit maps normalized states to normalized states. -/
theorem denote_preserves_normalization {n : Nat} (circuit : Circuit n)
    {state : State n} (normalized : IsNormalized state) :
    IsNormalized (denote circuit state) := by
  rw [IsNormalized, denote_preserves_normSquared, normalized]

end General
end QuantumValidation
