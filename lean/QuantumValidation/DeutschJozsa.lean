import QuantumValidation.GeneralCircuit
import QuantumValidation.GeneratedDj2Constant
import QuantumValidation.GeneratedDj2Balanced

/-!
Output discrimination for two fixed two-query-qubit Deutsch-Jozsa examples.

The generated modules prove exact circuit-to-target equality for f = 0 and
f(x0, x1) = x0. The lemmas below characterize those targets over `Basis 3`;
they do not quantify over all constant or balanced oracles or prove query complexity.

Qubits 0 and 1 are queries, and qubit 2 is the ancilla. The constant target
has support only on query 00; the balanced target has zero amplitude there.
These asymmetric targets also exercise the basis-order convention that
reversal-invariant Bell and GHZ targets cannot distinguish.
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
