import QuantumValidation.GeneralCircuit

/-!
Generated from circuit IR and contract schema version 0.1.
Regenerate this module instead of editing it by hand.
-/

namespace QuantumValidation
namespace General

/--
The three-qubit GHZ state:

    |GHZ₃⟩ = (|000⟩ + |111⟩) / √2.

A `State 3` maps each computational basis state to its amplitude.
`noncomputable` is needed because `invSqrtTwo` is an exact irrational value.
-/
noncomputable def Ghz3 : State 3 :=
  fun basis =>
    if basis 2 then
      if basis 1 then
        if basis 0 then
          invSqrtTwo  -- |111⟩
        else
          0           -- |110⟩
      else
        if basis 0 then
          0           -- |101⟩
        else
          0           -- |100⟩
    else
      if basis 1 then
        if basis 0 then
          0           -- |011⟩
        else
          0           -- |010⟩
      else
        if basis 0 then
          0           -- |001⟩
        else
          invSqrtTwo  -- |000⟩


/--
Circuit preparing `Ghz3` from `|000⟩`.

The Hadamard creates the superposition, while the two CNOT gates
propagate the value of the first qubit to the other qubits.
-/
def generatedGHZThreeQubitPreparationCircuit : Circuit 3 :=
  [
    .h 0,
    .cnot 0 1 (by decide),
    .cnot 1 2 (by decide)
  ]


/--
Initial state `|000⟩`.

Its amplitude is `1` for `|000⟩` and `0` for every other basis state.
-/
noncomputable def generatedGHZThreeQubitPreparationInput : State 3 :=
  fun basis =>
    if basis 2 then
      0
    else
      if basis 1 then
        0
      else
        if basis 0 then
          0
        else
          1  -- |000⟩


/-- Expected output state of the circuit. -/
noncomputable def generatedGHZThreeQubitPreparationTarget : State 3 :=
  Ghz3


/--
The circuit transforms `|000⟩` exactly into the three-qubit GHZ state.
-/
theorem generatedGHZThreeQubitPreparationCorrect :
    denote
        generatedGHZThreeQubitPreparationCircuit
        generatedGHZThreeQubitPreparationInput
      =
        generatedGHZThreeQubitPreparationTarget := by
  classical

  -- States are functions, so we compare their amplitudes pointwise.
  funext basis

  -- Enumerate the eight possible three-qubit basis states.
  cases bit0 : basis 0 <;>
    cases bit1 : basis 1 <;>
    cases bit2 : basis 2 <;>

  -- Evaluate the circuit for each basis state.
  simp [
    denote,
    generatedGHZThreeQubitPreparationCircuit,
    generatedGHZThreeQubitPreparationInput,
    generatedGHZThreeQubitPreparationTarget,
    Ghz3,
    Gate.apply,
    setBit,
    flipBit,
    bit0,
    bit1,
    bit2
  ]

end General
end QuantumValidation
