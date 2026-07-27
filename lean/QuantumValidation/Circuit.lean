import Mathlib.Data.Complex.Basic
import Mathlib.Data.Fin.VecNotation
import Mathlib.Analysis.Real.Sqrt

/-!
Concrete semantics for the two-qubit vertical slice.

The fixed dimension keeps the first trusted semantics small and reviewable.
General `n`-qubit embeddings are deliberately deferred until this definition
and its Qiskit ordering convention have been validated end to end.
-/

namespace QuantumValidation

open Complex

/-- A two-qubit pure state in Qiskit's little-endian basis order. -/
abbrev State2 := Fin 4 → ℂ

/-- The exact scalar used by Hadamard and Bell-state amplitudes. -/
noncomputable def invSqrtTwo : ℂ :=
  ((Real.sqrt 2 : ℝ) : ℂ)⁻¹

/--
The supported two-qubit gate syntax mirrors circuit IR version 0.1.
Operands are encoded in constructors, so invalid arities cannot be expressed.
-/
inductive Gate2 where
  | identity (target : Fin 2)
  | x (target : Fin 2)
  | z (target : Fin 2)
  | h (target : Fin 2)
  | cnot (control target : Fin 2)
  | swap
  deriving DecidableEq, Repr

/--
Apply one gate to amplitudes ordered as `|00⟩, |01⟩, |10⟩, |11⟩`.

Equal control and target operands are assigned identity semantics only to keep
this function total. The IR validator must reject that malformed CNOT before
formal translation.
-/
noncomputable def Gate2.apply : Gate2 → State2 → State2
  | .identity _, state => state
  | .x 0, state => ![state 1, state 0, state 3, state 2]
  | .x 1, state => ![state 2, state 3, state 0, state 1]
  | .z 0, state => ![state 0, -state 1, state 2, -state 3]
  | .z 1, state => ![state 0, state 1, -state 2, -state 3]
  | .h 0, state =>
      ![
        (state 0 + state 1) * invSqrtTwo,
        (state 0 - state 1) * invSqrtTwo,
        (state 2 + state 3) * invSqrtTwo,
        (state 2 - state 3) * invSqrtTwo
      ]
  | .h 1, state =>
      ![
        (state 0 + state 2) * invSqrtTwo,
        (state 1 + state 3) * invSqrtTwo,
        (state 0 - state 2) * invSqrtTwo,
        (state 1 - state 3) * invSqrtTwo
      ]
  | .cnot 0 1, state => ![state 0, state 3, state 2, state 1]
  | .cnot 1 0, state => ![state 0, state 1, state 3, state 2]
  | .cnot _ _, state => state
  | .swap, state => ![state 0, state 2, state 1, state 3]

/-- A circuit is an execution-ordered list of gates. -/
abbrev Circuit2 := List Gate2

/--
Execute gates from left to right, matching the operation order in the IR.
-/
noncomputable def denote (circuit : Circuit2) (input : State2) : State2 :=
  circuit.foldl (fun state gate => gate.apply state) input

end QuantumValidation
