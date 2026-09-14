import QuantumValidation.GeneralProperties
import Mathlib.Tactic.Ring

/-!
Small, kernel-checked examples of semantics-preserving circuit rewrites.

These theorems do not verify Qiskit's transpiler implementation. They certify
the mathematical rewrite that a transpiler may apply after the source and
optimized circuits have been translated to the formal gate language.
-/

namespace QuantumValidation
namespace General

/-- Two circuits are equivalent when they agree on every input state. -/
def CircuitEquivalent {n : Nat} (
    source candidate : Circuit n
) : Prop :=
  ∀ input, denote source input = denote candidate input

/-- Applying Hadamard twice to the same qubit leaves every state unchanged. -/
theorem h_apply_twice {n : Nat} (target : Fin n) (state : State n) :
    Gate.apply (.h target) (Gate.apply (.h target) state) = state := by
  funext basis
  by_cases bitValue : basis target
  · simp [Gate.apply, bitValue, setBit]
    ring_nf
    rw [← bitValue, Function.update_eq_self, pow_two, invSqrtTwo_sq]
    ring
  · have bitFalse : basis target = false := Bool.eq_false_of_not_eq_true bitValue
    simp [Gate.apply, bitValue, setBit]
    ring_nf
    rw [← bitFalse, Function.update_eq_self, pow_two, invSqrtTwo_sq]
    ring

/--
The source circuit `H; H` and its empty optimized form have identical
semantics on every input state.
-/
theorem duplicate_h_transpilation_correct {n : Nat}
    (target : Fin n) :
    CircuitEquivalent [.h target, .h target] [] := by
  intro input
  simp [denote, h_apply_twice]

end General
end QuantumValidation
