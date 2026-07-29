import QuantumValidation.GeneralCircuit

/-!
# Semantic laws for basic quantum gates

This file proves reusable properties of the gates defined in
`QuantumValidation.GeneralCircuit`.

The results hold for every register size and every input state.
They can be used to simplify circuits and prove circuit equivalences.
-/

namespace QuantumValidation
namespace General

/--
The identity gate preserves every state.

The result follows directly from the definition of `Gate.apply`.
-/
theorem identity_apply {n : Nat} (
    target : Fin n
) (
    state : State n
) :
    Gate.apply (.identity target) state = state := by
  rfl


/--
The Pauli-X gate is involutive.

`X` flips the target qubit. Applying it twice flips the same bit twice,
therefore restoring the original state.
-/
theorem x_involutive {n : Nat} (
    target : Fin n
) (
    state : State n
) :
    Gate.apply (.x target) (Gate.apply (.x target) state) =
      state := by

  -- States are functions, so compare amplitudes pointwise.
  funext basis

  -- Flipping the same bit twice restores the original basis state.
  simp [
    Gate.apply,
    flipBit,
    setBit
  ]


/--
The Pauli-Z gate is involutive.

`Z` leaves amplitudes unchanged when the target bit is `0`
and multiplies them by `-1` when it is `1`.

Applying it twice removes the phase because `(-1) * (-1) = 1`.
-/
theorem z_involutive {n : Nat} (
    target : Fin n
) (
    state : State n
) :
    Gate.apply (.z target) (Gate.apply (.z target) state) =
      state := by

  -- Compare the amplitudes of an arbitrary basis state.
  funext basis

  -- Split according to the value of the target qubit.
  by_cases bit : basis target <;>
    simp [
      Gate.apply,
      bit
    ]


/--
A valid CNOT gate is involutive.

If the control bit is `0`, CNOT acts as the identity.
If it is `1`, CNOT flips the target bit.

Applying the same CNOT twice therefore restores the original state.
The proof `distinct` ensures that control and target are different qubits.
-/
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

  -- Prove equality by comparing amplitudes pointwise.
  funext basis

  -- Split according to the value of the control qubit.
  by_cases bit : basis control <;>

    -- CNOT either does nothing twice or flips the target twice.
    simp [
      Gate.apply,
      bit,
      flipBit,
      setBit,
      distinct
    ]

end General
end QuantumValidation
