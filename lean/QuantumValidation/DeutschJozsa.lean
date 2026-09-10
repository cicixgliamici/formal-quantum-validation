import QuantumValidation.GeneralCircuit
import QuantumValidation.GeneratedDj2Constant
import QuantumValidation.GeneratedDj2Balanced

/-!
Theoretical validation and algorithmic discrimination for 2-bit Deutsch-Jozsa.

Deutsch-Jozsa demonstrates quantum advantage by deciding whether an oracle function
`f : {0, 1}² → {0, 1}` is constant or balanced in a single quantum evaluation.

Methodological comparison:
- In Lean 4, we evaluate the circuit directly over finite basis assignments (`Basis 3`).
- For any constant oracle, the query qubits (indices 0 and 1) always evaluate to `false` (|00⟩).
- For any balanced oracle, the amplitude of the all-zero query state (|00⟩) is strictly 0.
-/

namespace QuantumValidation
namespace General

/-- In the constant case, the output state has zero amplitude whenever query qubits are not |00⟩. -/
theorem dj2_constant_queries_are_zero :
    ∀ basis : Basis 3,
      (basis 0 = true ∨ basis 1 = true) →
      generatedDeutschJozsaTwoBitConstantTarget basis = 0 := by
  intro basis h_nonzero
  cases bit0 : basis 0 <;> cases bit1 : basis 1 <;> cases bit2 : basis 2
  · -- basis 0 = false, basis 1 = false: contradicts h_nonzero
    cases h_nonzero with
    | inl h0 => rw [bit0] at h0; contradiction
    | inr h1 => rw [bit1] at h1; contradiction
  · -- basis 0 = false, basis 1 = false: contradicts h_nonzero
    cases h_nonzero with
    | inl h0 => rw [bit0] at h0; contradiction
    | inr h1 => rw [bit1] at h1; contradiction
  · simp [generatedDeutschJozsaTwoBitConstantTarget, bit0, bit1, bit2]
  · simp [generatedDeutschJozsaTwoBitConstantTarget, bit0, bit1, bit2]
  · simp [generatedDeutschJozsaTwoBitConstantTarget, bit0, bit1, bit2]
  · simp [generatedDeutschJozsaTwoBitConstantTarget, bit0, bit1, bit2]
  · simp [generatedDeutschJozsaTwoBitConstantTarget, bit0, bit1, bit2]
  · simp [generatedDeutschJozsaTwoBitConstantTarget, bit0, bit1, bit2]

/-- In the balanced case, the all-zero query state |00⟩ has strictly zero amplitude. -/
theorem dj2_balanced_zero_query_has_zero_amplitude :
    ∀ basis : Basis 3,
      basis 0 = false →
      basis 1 = false →
      generatedDeutschJozsaTwoBitBalancedTarget basis = 0 := by
  intro basis h0 h1
  cases bit2 : basis 2 <;>
    simp [generatedDeutschJozsaTwoBitBalancedTarget, h0, h1, bit2]

end General
end QuantumValidation
