import QuantumValidation.GeneratedGhz3
import QuantumValidation.ParametricGhz

/-!
Kernel-checked regression obligations for the GHZ development.

Unlike Python tests, every declaration in this module is rechecked by Lean's
kernel during `lake build`. The concrete sizes protect common boundary cases,
while the final theorem checks that parametric GHZ correctness composes with
the independently proved circuit norm-preservation result.
-/

namespace QuantumValidation
namespace General

/-- A one-qubit register exercises the empty fan-out base case. -/
theorem ghz_one_qubit_regression :
    denote (ghzCircuit 1 (by decide)) (ket (prefixBasis 0)) =
      ghzState 1 :=
  ghz_correct 1 (by decide)

/-- Two qubits exercise the first nonempty fan-out step. -/
theorem ghz_two_qubit_regression :
    denote (ghzCircuit 2 (by decide)) (ket (prefixBasis 0)) =
      ghzState 2 :=
  ghz_correct 2 (by decide)

/-- Five qubits guard against accidentally specializing the proof to GHZ(3). -/
theorem ghz_five_qubit_regression :
    denote (ghzCircuit 5 (by decide)) (ket (prefixBasis 0)) =
      ghzState 5 :=
  ghz_correct 5 (by decide)

/--
The proved GHZ target has the same squared norm as its all-zero input.

This theorem deliberately combines two independent developments:
`ghz_correct` identifies the output, while `denote_preserves_normSquared`
establishes the physical invariant for every admitted circuit.
-/
theorem ghz_target_preserves_input_norm (n : Nat) (nonempty : 0 < n) :
    normSquared (ghzState n) =
      normSquared (ket (prefixBasis (n := n) 0)) := by
  rw [← ghz_correct n nonempty]
  exact denote_preserves_normSquared
    (ghzCircuit n nonempty)
    (ket (prefixBasis (n := n) 0))

end General
end QuantumValidation
