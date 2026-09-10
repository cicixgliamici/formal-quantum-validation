import QuantumValidation.GeneralUnitarity
import Mathlib.LinearAlgebra.Matrix.ConjTranspose
import Mathlib.LinearAlgebra.Matrix.Trace

/-!
Exact matrix regression tests, checked by Lean rather than floating-point code.

Python test classes observe numerical matrices and application reports. Here,
namespaces group theorem-based tests: Lean has no need for a unittest class or
runtime assertions. Every positive property and every counterexample must be
proved. Boolean indices denote the one-qubit basis: false = |0>, true = |1>.
Rows are output indices; columns are input indices.
-/

namespace QuantumValidation.MatrixTests

open QuantumValidation.General

abbrev QubitMatrix := Matrix Bool Bool ℂ

/-- Check both adjoint identities explicitly, matching the Python matrix tests. -/
def IsUnitaryMatrix (matrix : QubitMatrix) : Prop :=
  matrix.conjTranspose * matrix = 1 ∧ matrix * matrix.conjTranspose = 1

/-- Pauli X exchanges the two basis amplitudes. -/
def xMatrix : QubitMatrix := fun row column => if row = !column then 1 else 0

/-- Pauli Z changes the sign of the |1> amplitude. -/
def zMatrix : QubitMatrix :=
  fun row column => if row = column then (if row then -1 else 1) else 0

/-- The exact Hadamard matrix uses the same scalar as the formal gate semantics. -/
noncomputable def hMatrix : QubitMatrix :=
  fun row column => if row && column then -invSqrtTwo else invSqrtTwo

/-- A complex diagnostic example; this phase gate is not part of IR 0.1. -/
def phaseMatrix : QubitMatrix :=
  fun row column => if row = column then (if row then Complex.I else 1) else 0

namespace Unitarity

/-- The irrational scalar is real, so complex conjugation leaves it unchanged. -/
private theorem invSqrtTwo_real : (starRingEnd ℂ) invSqrtTwo = invSqrtTwo := by
  simp [invSqrtTwo]

/-- This exact scalar identity replaces numerical tolerance in the Hadamard test. -/
private theorem invSqrtTwo_squared : invSqrtTwo * invSqrtTwo = (2 : ℂ)⁻¹ := by
  have square : (Real.sqrt 2 : ℂ) * (Real.sqrt 2 : ℂ) = 2 := by
    norm_cast
    exact Real.mul_self_sqrt (by norm_num)
  calc
    _ = ((Real.sqrt 2 : ℂ) * (Real.sqrt 2 : ℂ))⁻¹ := by
      simp only [invSqrtTwo, mul_inv_rev]
    _ = _ := congrArg Inv.inv square

/-- Identity satisfies the matrix definition without enumerating entries. -/
theorem identity_unitary : IsUnitaryMatrix (1 : QubitMatrix) := by
  simp [IsUnitaryMatrix]

/-- Enumerating four entries suffices for this exact two-dimensional check. -/
theorem x_unitary : IsUnitaryMatrix xMatrix := by
  constructor <;> ext row column <;> cases row <;> cases column <;>
    norm_num [xMatrix, Matrix.mul_apply, Matrix.conjTranspose_apply, Matrix.one_apply]

/-- Negative amplitudes must still have squared magnitude one. -/
theorem z_unitary : IsUnitaryMatrix zMatrix := by
  constructor <;> ext row column <;> cases row <;> cases column <;>
    norm_num [zMatrix, Matrix.mul_apply, Matrix.conjTranspose_apply, Matrix.one_apply]

/-- A genuinely complex entry exercises conjugation, not just transposition. -/
theorem phase_unitary : IsUnitaryMatrix phaseMatrix := by
  constructor <;> ext row column <;> cases row <;> cases column <;>
    norm_num [phaseMatrix, Matrix.mul_apply, Matrix.conjTranspose_apply, Matrix.one_apply]

/-- The 1/sqrt(2) normalization is essential for both adjoint identities. -/
theorem h_unitary : IsUnitaryMatrix hMatrix := by
  constructor <;> ext row column <;> cases row <;> cases column <;>
    norm_num [hMatrix, Matrix.mul_apply, Matrix.conjTranspose_apply,
      Matrix.one_apply, invSqrtTwo_real, invSqrtTwo_squared]

/-- Hadamard is also self-adjoint, a stronger property than unitarity alone. -/
theorem h_self_adjoint : hMatrix.conjTranspose = hMatrix := by
  ext row column
  cases row <;> cases column <;>
    simp [hMatrix, Matrix.conjTranspose_apply, invSqrtTwo_real]

/-- Combine the previous properties to prove exact self-inversion. -/
theorem h_self_inverse : hMatrix * hMatrix = 1 := by
  simpa only [h_self_adjoint] using h_unitary.1

end Unitarity

namespace GateCorrespondence

/-- Connect a two-entry column vector to the existing one-qubit state model. -/
def encodeState (amplitudes : Bool → ℂ) : State 1 :=
  fun basis => amplitudes (basis 0)

/-- Matrix multiplication must agree with the production X semantics on any state. -/
theorem x_action (amplitudes : Bool → ℂ) (bit : Bool) :
    (xMatrix.mulVec amplitudes) bit =
      Gate.apply (.x 0) (encodeState amplitudes) (fun _ => bit) := by
  cases bit <;>
    simp [xMatrix, Matrix.mulVec, dotProduct, Gate.apply, encodeState, flipBit, setBit]

/-- The correspondence includes phases of arbitrary complex input amplitudes. -/
theorem z_action (amplitudes : Bool → ℂ) (bit : Bool) :
    (zMatrix.mulVec amplitudes) bit =
      Gate.apply (.z 0) (encodeState amplitudes) (fun _ => bit) := by
  cases bit <;>
    simp [zMatrix, Matrix.mulVec, dotProduct, Gate.apply, encodeState]

/-- This links the handwritten Hadamard matrix to the actual gate implementation. -/
theorem h_action (amplitudes : Bool → ℂ) (bit : Bool) :
    (hMatrix.mulVec amplitudes) bit =
      Gate.apply (.h 0) (encodeState amplitudes) (fun _ => bit) := by
  cases bit <;>
    simp [hMatrix, Matrix.mulVec, dotProduct, Gate.apply, encodeState, setBit] <;> ring

/-- Lift the pointwise comparison so existing semantic invariants can be reused. -/
theorem h_encoded_action (amplitudes : Bool → ℂ) :
    encodeState (hMatrix.mulVec amplitudes) = Gate.apply (.h 0) (encodeState amplitudes) := by
  funext basis
  change (hMatrix.mulVec amplitudes) (basis 0) = _
  rw [h_action]
  have sameBasis : (fun _ : Fin 1 => basis 0) = basis := by
    funext index
    fin_cases index
    rfl
  rw [sameBasis]

/-- The handwritten matrix inherits norm preservation from the verified gate. -/
theorem h_preserves_norm (amplitudes : Bool → ℂ) :
    normSquared (encodeState (hMatrix.mulVec amplitudes)) =
      normSquared (encodeState amplitudes) := by
  rw [h_encoded_action]
  exact (QuantumValidation.General.h_unitary 0).preserves_normSquared _

/-- The bridge covers arbitrary pairs of complex vectors, not just basis inputs. -/
theorem h_preserves_inner (left right : Bool → ℂ) :
    inner (encodeState (hMatrix.mulVec left)) (encodeState (hMatrix.mulVec right)) =
      inner (encodeState left) (encodeState right) := by
  rw [h_encoded_action, h_encoded_action]
  exact QuantumValidation.General.h_unitary 0 _ _

end GateCorrespondence

namespace Counterexamples

/-- Both columns have length one, but they are identical rather than orthogonal. -/
def duplicateColumns : QubitMatrix := fun row _ => if row then 0 else 1

/-- Looking at an off-diagonal Gram entry exposes the missing orthogonality. -/
theorem duplicate_columns_not_unitary : ¬ IsUnitaryMatrix duplicateColumns := by
  intro property
  have offDiagonal := congrFun (congrFun property.1 false) true
  norm_num [duplicateColumns, Matrix.mul_apply, Matrix.conjTranspose_apply,
    Matrix.one_apply] at offDiagonal

/-- Normalized basis images alone do not ensure preservation of superpositions. -/
theorem duplicate_columns_destroy_difference :
    duplicateColumns.mulVec (fun bit => if bit then (-1 : ℂ) else 1) = 0 := by
  ext bit
  cases bit <;> norm_num [duplicateColumns, Matrix.mulVec, dotProduct]

/-- A diagonal scaling changes norms even though the matrix is invertible. -/
def scaledIdentity : QubitMatrix := fun row column => if row = column then 2 else 0

/-- A diagonal Gram entry becomes four rather than the required one. -/
theorem scaled_identity_not_unitary : ¬ IsUnitaryMatrix scaledIdentity := by
  intro property
  have diagonal := congrFun (congrFun property.1 false) false
  norm_num [scaledIdentity, Matrix.mul_apply, Matrix.conjTranspose_apply, map_ofNat,
    Matrix.one_apply] at diagonal

/-- Dropping conjugation incorrectly rejects a valid complex unitary matrix. -/
theorem transpose_is_not_the_adjoint :
    phaseMatrix.transpose * phaseMatrix ≠ (1 : QubitMatrix) := by
  intro equality
  have diagonal := congrFun (congrFun equality true) true
  norm_num [phaseMatrix, Matrix.mul_apply, Matrix.transpose_apply,
    Matrix.one_apply] at diagonal

end Counterexamples

namespace AdvancedProperties

/-- Pauli X is traceless. -/
theorem x_traceless : Matrix.trace xMatrix = 0 := by
  simp [Matrix.trace, xMatrix]

/-- Pauli Z is traceless. -/
theorem z_traceless : Matrix.trace zMatrix = 0 := by
  simp [Matrix.trace, zMatrix]

/-- Pauli X is self-adjoint. -/
theorem x_self_adjoint : xMatrix.conjTranspose = xMatrix := by
  ext row column
  cases row <;> cases column <;>
    simp [xMatrix, Matrix.conjTranspose_apply]

/-- Pauli Z is self-adjoint. -/
theorem z_self_adjoint : zMatrix.conjTranspose = zMatrix := by
  ext row column
  cases row <;> cases column <;>
    simp [zMatrix, Matrix.conjTranspose_apply]

end AdvancedProperties

namespace TwoQubit

abbrev TwoQubitMatrix := Matrix (Bool × Bool) (Bool × Bool) ℂ

/-- Two-qubit unitary definition -/
def IsTwoQubitUnitaryMatrix (matrix : TwoQubitMatrix) : Prop :=
  matrix.conjTranspose * matrix = 1 ∧ matrix * matrix.conjTranspose = 1

/-- CNOT with control 0 and target 1. -/
def cnotMatrix : TwoQubitMatrix :=
  fun row column => if row = (column.1, if column.1 then !column.2 else column.2) then 1 else 0

/-- SWAP exchanges the two qubits. -/
def swapMatrix : TwoQubitMatrix :=
  fun row column => if row = (column.2, column.1) then 1 else 0

/-- CNOT is unitary. -/
theorem cnot_unitary : IsTwoQubitUnitaryMatrix cnotMatrix := by
  constructor <;> ext ⟨r1, r2⟩ ⟨c1, c2⟩ <;> cases r1 <;> cases r2 <;> cases c1 <;> cases c2 <;>
    simp [cnotMatrix, Matrix.mul_apply, Matrix.conjTranspose_apply, Fintype.sum_prod_type]

/-- SWAP is unitary. -/
theorem swap_unitary : IsTwoQubitUnitaryMatrix swapMatrix := by
  constructor <;> ext ⟨r1, r2⟩ ⟨c1, c2⟩ <;> cases r1 <;> cases r2 <;> cases c1 <;> cases c2 <;>
    simp [swapMatrix, Matrix.mul_apply, Matrix.conjTranspose_apply, Fintype.sum_prod_type]

end TwoQubit

end QuantumValidation.MatrixTests
