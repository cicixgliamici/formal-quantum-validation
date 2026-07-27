import QuantumValidation.GeneralCircuit

/-!
Reusable semantic laws for the general finite circuit model.

These lemmas hold for every register size and state. They form a small algebraic
base for later normalization and unitarity proofs.
-/

namespace QuantumValidation
namespace General

/-- The identity gate preserves every state. -/
theorem identity_apply {n : Nat} (
    target : Fin n
) (
    state : State n
) :
    Gate.apply (.identity target) state = state := by
  rfl

/-- Applying `X` twice to the same target restores every state. -/
theorem x_involutive {n : Nat} (
    target : Fin n
) (
    state : State n
) :
    Gate.apply (.x target) (Gate.apply (.x target) state) =
      state := by
  funext basis
  simp [Gate.apply, flipBit, setBit]

/-- Applying `Z` twice to the same target restores every state. -/
theorem z_involutive {n : Nat} (
    target : Fin n
) (
    state : State n
) :
    Gate.apply (.z target) (Gate.apply (.z target) state) =
      state := by
  funext basis
  by_cases bit : basis target <;>
    simp [Gate.apply, bit]

/-- Applying one valid CNOT twice restores every state. -/
theorem cnot_involutive {n : Nat} (
    control target : Fin n
) (
    distinct : control ≠ target
) (
    state : State n
) :
    Gate.apply
        (.cnot control target distinct)
        (Gate.apply (.cnot control target distinct) state) =
      state := by
  funext basis
  by_cases bit : basis control <;>
    simp [
      Gate.apply,
      bit,
      flipBit,
      setBit,
      distinct
    ]

end General
end QuantumValidation
