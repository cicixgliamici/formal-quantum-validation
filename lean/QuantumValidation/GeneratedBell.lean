import QuantumValidation.GeneralCircuit

/-!
Generated from circuit IR and contract schema version 0.1.
Regenerate this module instead of editing it by hand.
-/

namespace QuantumValidation
namespace General

def generatedBellStatePreparationCircuit : Circuit 2 :=
  [.h 0, .cnot 0 1 (by decide)]

noncomputable def generatedBellStatePreparationInput : State 2 :=
  fun basis => (if basis 1 then (if basis 0 then 0 else 0) else (if basis 0 then 0 else 1))

noncomputable def generatedBellStatePreparationTarget : State 2 :=
  fun basis => (if basis 1 then (if basis 0 then invSqrtTwo else 0) else (if basis 0 then 0 else invSqrtTwo))

theorem generatedBellStatePreparationCorrect :
    denote generatedBellStatePreparationCircuit generatedBellStatePreparationInput = generatedBellStatePreparationTarget := by
  classical
  funext basis
  cases bit0 : basis 0 <;> cases bit1 : basis 1 <;>
    simp [
      denote,
      generatedBellStatePreparationCircuit,
      generatedBellStatePreparationInput,
      generatedBellStatePreparationTarget,
      Gate.apply,
      setBit,
      flipBit,
      bit0, bit1
    ]

end General
end QuantumValidation
