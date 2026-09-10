import QuantumValidation.GeneralCircuit
import Mathlib.Tactic.Ring

/-!
Generated from circuit IR and contract schema version 0.1.
Regenerate this module instead of editing it by hand.
-/

namespace QuantumValidation
namespace General

theorem invSqrtTwo_sq : invSqrtTwo * invSqrtTwo = (2 : ℂ)⁻¹ := by
  have square : (Real.sqrt 2 : ℂ) * (Real.sqrt 2 : ℂ) = 2 := by
    norm_cast
    exact Real.mul_self_sqrt (by norm_num)
  calc
    _ = ((Real.sqrt 2 : ℂ) * (Real.sqrt 2 : ℂ))⁻¹ := by
      simp only [invSqrtTwo, mul_inv_rev]
    _ = _ := congrArg Inv.inv square

/-- Gate order is copied from the validated circuit IR. -/
def generatedDeutschJozsaTwoBitConstantCircuit : Circuit 3 :=
  [.x 2, .h 0, .h 1, .h 2, .h 0, .h 1]

/-- Exact input amplitudes in little-endian basis order. -/
noncomputable def generatedDeutschJozsaTwoBitConstantInput : State 3 :=
  fun basis => (if basis 2 then (if basis 1 then (if basis 0 then 0 else 0) else (if basis 0 then 0 else 0)) else (if basis 1 then (if basis 0 then 0 else 0) else (if basis 0 then 0 else 1)))

/-- Exact target amplitudes; global phase is part of the specification. -/
noncomputable def generatedDeutschJozsaTwoBitConstantTarget : State 3 :=
  fun basis => (if basis 2 then (if basis 1 then (if basis 0 then 0 else 0) else (if basis 0 then 0 else -invSqrtTwo)) else (if basis 1 then (if basis 0 then 0 else 0) else (if basis 0 then 0 else invSqrtTwo)))

/-- This obligation proves state preparation, not resource or sampling fields. -/
theorem generatedDeutschJozsaTwoBitConstantCorrect :
    denote generatedDeutschJozsaTwoBitConstantCircuit generatedDeutschJozsaTwoBitConstantInput = generatedDeutschJozsaTwoBitConstantTarget := by
  classical
  -- Function extensionality reduces state equality to amplitudes.
  funext basis
  have h2 : invSqrtTwo * invSqrtTwo = (2 : ℂ)⁻¹ := invSqrtTwo_sq
  -- Exhaustive basis cases over all 8 assignments.
  cases bit0 : basis 0 <;> cases bit1 : basis 1 <;> cases bit2 : basis 2
  · -- basis = 000 (amplitude +invSqrtTwo)
    simp [
      denote,
      generatedDeutschJozsaTwoBitConstantCircuit,
      generatedDeutschJozsaTwoBitConstantInput,
      generatedDeutschJozsaTwoBitConstantTarget,
      Gate.apply,
      setBit,
      flipBit,
      bit0, bit1, bit2
    ]
    have h_alg : ((invSqrtTwo * invSqrtTwo * invSqrtTwo + invSqrtTwo * invSqrtTwo * invSqrtTwo) * invSqrtTwo +
          (invSqrtTwo * invSqrtTwo * invSqrtTwo + invSqrtTwo * invSqrtTwo * invSqrtTwo) * invSqrtTwo) *
        invSqrtTwo = 4 * (invSqrtTwo * invSqrtTwo) * (invSqrtTwo * invSqrtTwo) * invSqrtTwo := by ring
    rw [h_alg, h2]
    ring
  · -- basis = 100 (amplitude -invSqrtTwo)
    simp [
      denote,
      generatedDeutschJozsaTwoBitConstantCircuit,
      generatedDeutschJozsaTwoBitConstantInput,
      generatedDeutschJozsaTwoBitConstantTarget,
      Gate.apply,
      setBit,
      flipBit,
      bit0, bit1, bit2
    ]
    have h_alg : ((-(invSqrtTwo * invSqrtTwo * invSqrtTwo) + -(invSqrtTwo * invSqrtTwo * invSqrtTwo)) * invSqrtTwo +
          (-(invSqrtTwo * invSqrtTwo * invSqrtTwo) + -(invSqrtTwo * invSqrtTwo * invSqrtTwo)) * invSqrtTwo) *
        invSqrtTwo = - (4 * (invSqrtTwo * invSqrtTwo) * (invSqrtTwo * invSqrtTwo) * invSqrtTwo) := by ring
    rw [h_alg, h2]
    ring
  · simp [denote, generatedDeutschJozsaTwoBitConstantCircuit, generatedDeutschJozsaTwoBitConstantInput, generatedDeutschJozsaTwoBitConstantTarget, Gate.apply, setBit, flipBit, bit0, bit1, bit2]
  · simp [denote, generatedDeutschJozsaTwoBitConstantCircuit, generatedDeutschJozsaTwoBitConstantInput, generatedDeutschJozsaTwoBitConstantTarget, Gate.apply, setBit, flipBit, bit0, bit1, bit2]
  · simp [denote, generatedDeutschJozsaTwoBitConstantCircuit, generatedDeutschJozsaTwoBitConstantInput, generatedDeutschJozsaTwoBitConstantTarget, Gate.apply, setBit, flipBit, bit0, bit1, bit2]
  · simp [denote, generatedDeutschJozsaTwoBitConstantCircuit, generatedDeutschJozsaTwoBitConstantInput, generatedDeutschJozsaTwoBitConstantTarget, Gate.apply, setBit, flipBit, bit0, bit1, bit2]
  · simp [denote, generatedDeutschJozsaTwoBitConstantCircuit, generatedDeutschJozsaTwoBitConstantInput, generatedDeutschJozsaTwoBitConstantTarget, Gate.apply, setBit, flipBit, bit0, bit1, bit2]
  · simp [denote, generatedDeutschJozsaTwoBitConstantCircuit, generatedDeutschJozsaTwoBitConstantInput, generatedDeutschJozsaTwoBitConstantTarget, Gate.apply, setBit, flipBit, bit0, bit1, bit2]

end General
end QuantumValidation
