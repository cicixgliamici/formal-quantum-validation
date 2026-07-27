import QuantumValidation.GeneralCircuit

/-!
Generated from circuit IR and contract schema version 0.1.
Regenerate this module instead of editing it by hand.
-/

namespace QuantumValidation
namespace General

def generatedGHZThreeQubitPreparationCircuit : Circuit 3 :=
  [.h 0, .cnot 0 1 (by decide), .cnot 1 2 (by decide)]

noncomputable def generatedGHZThreeQubitPreparationInput : State 3 :=
  fun basis => (if basis 2 then (if basis 1 then (if basis 0 then 0 else 0) else (if basis 0 then 0 else 0)) else (if basis 1 then (if basis 0 then 0 else 0) else (if basis 0 then 0 else 1)))

noncomputable def generatedGHZThreeQubitPreparationTarget : State 3 :=
  fun basis => (if basis 2 then (if basis 1 then (if basis 0 then invSqrtTwo else 0) else (if basis 0 then 0 else 0)) else (if basis 1 then (if basis 0 then 0 else 0) else (if basis 0 then 0 else invSqrtTwo)))

theorem generatedGHZThreeQubitPreparationCorrect :
    denote generatedGHZThreeQubitPreparationCircuit generatedGHZThreeQubitPreparationInput = generatedGHZThreeQubitPreparationTarget := by
  classical
  funext basis
  cases bit0 : basis 0 <;> cases bit1 : basis 1 <;> cases bit2 : basis 2 <;>
    simp [
      denote,
      generatedGHZThreeQubitPreparationCircuit,
      generatedGHZThreeQubitPreparationInput,
      generatedGHZThreeQubitPreparationTarget,
      Gate.apply,
      setBit,
      flipBit,
      bit0, bit1, bit2
    ]

end General
end QuantumValidation
