import QuantumValidation.Circuit
import Mathlib.Tactic.FinCases

/-!
Machine-checked correctness of Bell-state preparation.
-/

namespace QuantumValidation

/-- The Qiskit circuit `h(0); cx(0, 1)` represented as formal data. -/
def bellCircuit : Circuit2 :=
  [.h 0, .cnot 0 1]

/-- The all-zero input state in Qiskit's little-endian basis order. -/
def ket00 : State2 :=
  ![1, 0, 0, 0]

/-- The expected Bell state `( |00⟩ + |11⟩ ) / √2`. -/
noncomputable def phiPlus : State2 :=
  ![invSqrtTwo, 0, 0, invSqrtTwo]

/--
The Bell circuit maps the all-zero input to `|Φ+⟩`.

The proof unfolds the general circuit and gate semantics, then checks all four
amplitudes. No Bell-specific semantic axiom is used.
-/
theorem bell_correct :
    denote bellCircuit ket00 = phiPlus := by
  funext index
  fin_cases index <;>
    simp [denote, bellCircuit, ket00, phiPlus, Gate2.apply]

end QuantumValidation
