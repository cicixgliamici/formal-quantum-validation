import QuantumValidation.GeneralCircuit

/-!
Generated from circuit IR and contract schema version 0.1.
Regenerate this module instead of editing it by hand.
-/

namespace QuantumValidation
namespace General

/--
The Bell state:

    |Φ⁺⟩ = (|00⟩ + |11⟩) / √2.

A `State 2` maps each computational basis state to its amplitude.
`noncomputable` is needed because `invSqrtTwo` is an exact irrational value.
-/
noncomputable def Bell2 : State 2 :=
  fun basis =>
    if basis 1 then
      if basis 0 then
        invSqrtTwo  -- |11⟩
      else
        0           -- |10⟩
    else
      if basis 0 then
        0           -- |01⟩
      else
        invSqrtTwo  -- |00⟩


/--
Circuit preparing `Bell2` from `|00⟩`.

The Hadamard creates the superposition, while the CNOT entangles
the second qubit with the first one.
-/
def generatedBellStatePreparationCircuit : Circuit 2 :=
  [
    .h 0,
    .cnot 0 1 (by decide)
  ]


/--
Initial state `|00⟩`.

Its amplitude is `1` for `|00⟩` and `0` for every other basis state.
-/
noncomputable def generatedBellStatePreparationInput : State 2 :=
  fun basis =>
    if basis 1 then
      0
    else
      if basis 0 then
        0
      else
        1  -- |00⟩


/-- Expected output state of the circuit. -/
noncomputable def generatedBellStatePreparationTarget : State 2 :=
  Bell2


/--
The circuit transforms `|00⟩` exactly into the Bell state `|Φ⁺⟩`.
-/
theorem generatedBellStatePreparationCorrect :
    denote
        generatedBellStatePreparationCircuit
        generatedBellStatePreparationInput
      =
        generatedBellStatePreparationTarget := by
  classical

  -- States are functions, so we compare their amplitudes pointwise.
  funext basis

  -- Enumerate the four possible two-qubit basis states.
  cases bit0 : basis 0 <;>
    cases bit1 : basis 1 <;>

  -- Evaluate the circuit for each basis state.
  simp [
    denote,
    generatedBellStatePreparationCircuit,
    generatedBellStatePreparationInput,
    generatedBellStatePreparationTarget,
    Bell2,
    Gate.apply,
    setBit,
    flipBit,
    bit0,
    bit1
  ]

end General
end QuantumValidation
