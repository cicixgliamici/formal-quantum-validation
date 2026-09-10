import QuantumValidation.GeneralCircuit

/-!
Generated from circuit IR and contract schema version 0.1.
Regenerate this module instead of editing it by hand.
-/

namespace QuantumValidation
namespace General

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
  -- Exhaustive basis cases are intended only for small fixed-size circuits.
  cases bit0 : basis 0 <;> cases bit1 : basis 1 <;> cases bit2 : basis 2 <;>
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

end General
end QuantumValidation
