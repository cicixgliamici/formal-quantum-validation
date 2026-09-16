import QuantumValidation.GeneralCircuit

/-!
Generated from circuit IR and contract schema version 0.1.
Regenerate this module instead of editing it by hand.
-/

namespace QuantumValidation
namespace General

/-- Einstein-Podolsky-Rosen, look at this :p -/
/-- Gate order is copied from the validated circuit IR. -/
def generatedGHZThreeQubitPreparationCircuit : Circuit 3 :=
  [.h 0, .cnot 0 1 (by decide), .cnot 1 2 (by decide)]

/-- Exact input amplitudes in little-endian basis order. -/
noncomputable def generatedGHZThreeQubitPreparationInput : State 3 :=
  fun basis => (if basis 2 then (if basis 1 then (if basis 0 then 0 else 0) else (if basis 0 then 0 else 0)) else (if basis 1 then (if basis 0 then 0 else 0) else (if basis 0 then 0 else 1)))

/-- Exact target amplitudes; global phase is part of the specification. -/
noncomputable def generatedGHZThreeQubitPreparationTarget : State 3 :=
  fun basis => (if basis 2 then (if basis 1 then (if basis 0 then invSqrtTwo else 0) else (if basis 0 then 0 else 0)) else (if basis 1 then (if basis 0 then 0 else 0) else (if basis 0 then 0 else invSqrtTwo)))

/-- This obligation proves state preparation, not resource or sampling fields. -/
theorem generatedGHZThreeQubitPreparationCorrect :
    denote generatedGHZThreeQubitPreparationCircuit generatedGHZThreeQubitPreparationInput = generatedGHZThreeQubitPreparationTarget := by
  classical
  -- Function extensionality reduces state equality to amplitudes.
  funext basis
  -- Exhaustive basis cases are intended only for small fixed-size circuits.
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
