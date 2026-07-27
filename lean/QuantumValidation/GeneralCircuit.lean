import Mathlib.Analysis.Real.Sqrt
import Mathlib.Data.Complex.Basic

/-!
General finite pure-state semantics for the supported unitary circuit fragment.

A computational-basis element is a Boolean assignment to `n` qubit positions.
Position zero is the least significant Qiskit qubit. This representation keeps
bit ordering explicit and avoids unchecked arithmetic conversions.
-/

namespace QuantumValidation
namespace General

open Complex

/-- One computational-basis assignment for an `n`-qubit register. -/
abbrev Basis (n : Nat) := Fin n → Bool

/-- An `n`-qubit pure state maps each basis assignment to one amplitude. -/
abbrev State (n : Nat) := Basis n → ℂ

/-- The exact scalar shared by Hadamard and common entangled states. -/
noncomputable def invSqrtTwo : ℂ :=
  ((Real.sqrt 2 : ℝ) : ℂ)⁻¹

/-- Replace one qubit value in a computational-basis assignment. -/
def setBit {n : Nat} (
    basis : Basis n
) (
    target : Fin n
) (
    value : Bool
) : Basis n :=
  Function.update basis target value

/-- Flip one qubit in a computational-basis assignment. -/
def flipBit {n : Nat} (
    basis : Basis n
) (
    target : Fin n
) : Basis n :=
  setBit basis target (!(basis target))

/--
The general gate syntax mirrors circuit IR version 0.1.

Proof fields make malformed two-qubit operations unrepresentable after the
Python boundary validator has accepted their operands.
-/
inductive Gate (n : Nat) where
  | identity (target : Fin n)
  | x (target : Fin n)
  | z (target : Fin n)
  | h (target : Fin n)
  | cnot (
      control target : Fin n
    ) (
      distinct : control ≠ target
    )
  | swap (
      left right : Fin n
    ) (
      distinct : left ≠ right
    )

/--
Apply a gate to amplitudes.

Permutation gates read the amplitude at the inverse basis permutation. `X`,
`CNOT`, and `SWAP` are self-inverse, which keeps their definitions compact.
-/
noncomputable def Gate.apply {n : Nat} :
    Gate n → State n → State n
  | .identity _, state => state
  | .x target, state =>
      fun basis => state (flipBit basis target)
  | .z target, state =>
      fun basis =>
        if basis target then
          -state basis
        else
          state basis
  | .h target, state =>
      fun basis =>
        let zeroAmplitude :=
          state (setBit basis target false)
        let oneAmplitude :=
          state (setBit basis target true)
        if basis target then
          (zeroAmplitude - oneAmplitude) * invSqrtTwo
        else
          (zeroAmplitude + oneAmplitude) * invSqrtTwo
  | .cnot control target _, state =>
      fun basis =>
        if basis control then
          state (flipBit basis target)
        else
          state basis
  | .swap left right _, state =>
      fun basis =>
        state (
          setBit
            (setBit basis left (basis right))
            right
            (basis left)
        )

/-- A general circuit is an execution-ordered list of well-formed gates. -/
abbrev Circuit (n : Nat) := List (Gate n)

/-- Execute circuit gates from left to right, matching circuit IR order. -/
noncomputable def denote {n : Nat} (
    circuit : Circuit n
) (
    input : State n
) : State n :=
  circuit.foldl (fun state gate => gate.apply state) input

end General
end QuantumValidation
