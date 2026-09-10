"""Regression cases for malformed specifications and exact translation."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter

from fqv.backend.lean.generator import generate_lean_module, write_lean_module
from fqv.cli import main
from fqv.domain.contract_parser import contract_from_dict
from fqv.domain.contract_validation import InvalidContractError
from fqv.domain.reports import VerificationReport
from fqv.frontend.qiskit.checks.state import check_target_state
from fqv.frontend.qiskit.circuits import bell_contract, build_bell_circuit
from fqv.frontend.qiskit.extraction import UnsupportedCircuitError, circuit_to_ir
from fqv.frontend.qiskit.verification import verify_contract
from fqv.ir.checked import CheckedCircuitIr, CheckedOperation, GateName
from fqv.ir.validation import InvalidIrError, check_ir
from fqv.pipeline.transpilation import TranspilationConfig, check_operator_equivalence

PROJECT_ROOT = Path(__file__).parents[1]


def _contract() -> dict:
    """Load a fresh fixture so mutations cannot leak between tests."""
    path = PROJECT_ROOT / "src/fqv/data/bell.contract.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("field", ["initial_state", "target_state"])
@pytest.mark.parametrize("tokens", [["one"] * 4, ["zero"] * 4])
def test_parser_rejects_unnormalized_states(field: str, tokens: list[str]) -> None:
    data = _contract()
    data[field] = tokens
    with pytest.raises(InvalidContractError, match="normalized"):
        contract_from_dict(data)


def test_direct_contract_cannot_report_fidelity_above_one() -> None:
    # Reproduce the previous PASS with fidelity=4 through the public Python API.
    contract = replace(bell_contract(), initial_state=(1, 1, 0, 0),
                       target_state=(1, 1, 0, 0))
    report = VerificationReport(contract_name=contract.name)
    with pytest.raises(InvalidContractError, match="normalized"):
        check_target_state(QuantumCircuit(2), contract, report)
    assert not report.checks


@pytest.mark.parametrize("field", ["exact_tolerance", "sampled_tolerance"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), 10**400])
def test_parser_rejects_nonfinite_tolerances(field: str, value: float) -> None:
    data = _contract()
    data["probabilities"][0][field] = value
    with pytest.raises(InvalidContractError):
        contract_from_dict(data)


@pytest.mark.parametrize("location", ["root", "resources", "probability"])
def test_contract_rejects_unknown_fields(location: str) -> None:
    data = _contract()
    container = {"root": data, "resources": data["resources"],
                 "probability": data["probabilities"][0]}[location]
    container["typo"] = 1
    with pytest.raises(InvalidContractError, match="unexpected fields"):
        contract_from_dict(data)


def test_contract_requires_schema_resource_fields() -> None:
    data = _contract()
    del data["resources"]["allow_extra_gates"]
    with pytest.raises(InvalidContractError, match="missing fields"):
        contract_from_dict(data)


@pytest.mark.parametrize("value", [None, [], "invalid"])
def test_public_parsers_reject_non_object_roots(value: object) -> None:
    with pytest.raises(InvalidContractError, match="JSON object"):
        contract_from_dict(value)
    with pytest.raises(InvalidIrError, match="JSON object"):
        check_ir(value)


@pytest.mark.parametrize("field", ["controls", "params", "condition"])
def test_ir_rejects_unrepresentable_gate_fields(field: str) -> None:
    ir = circuit_to_ir(build_bell_circuit())
    ir["operations"][0][field] = [1]
    with pytest.raises(InvalidIrError, match="unexpected fields"):
        check_ir(ir)


def test_ir_rejects_unknown_root_fields() -> None:
    ir = circuit_to_ir(build_bell_circuit())
    ir["global_phase"] = 1.0
    with pytest.raises(InvalidIrError, match="unexpected fields"):
        check_ir(ir)


@pytest.mark.parametrize("phase", [np.pi, np.pi / 2, 1e-15, Parameter("phase")])
def test_ir_export_rejects_global_phase(phase: object) -> None:
    circuit = build_bell_circuit()
    circuit.global_phase = phase
    with pytest.raises(UnsupportedCircuitError, match="Global phase"):
        circuit_to_ir(circuit)


def test_ir_export_rejects_unmapped_layout() -> None:
    circuit = transpile(build_bell_circuit(), initial_layout=[1, 0],
                        optimization_level=0)
    assert circuit.layout is not None
    with pytest.raises(UnsupportedCircuitError, match="logical remapping"):
        circuit_to_ir(circuit)


def test_default_cli_works_outside_checkout(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["fqv-verify"])
    assert main() == 0
    assert "Overall result: PASS" in capsys.readouterr().out


@pytest.mark.parametrize("field", ["shots", "seed"])
@pytest.mark.parametrize("value", [True, 1.5, -1])
def test_sampling_configuration_rejects_invalid_integers(field: str, value: object) -> None:
    with pytest.raises(ValueError, match="integer"):
        verify_contract(build_bell_circuit(), bell_contract(), **{field: value})


@pytest.mark.parametrize("field", ["optimization_level", "seed_transpiler"])
@pytest.mark.parametrize("value", [True, 1.5, -1])
def test_transpilation_configuration_rejects_invalid_integers(field: str, value: object) -> None:
    with pytest.raises(ValueError):
        TranspilationConfig(**{field: value})


def test_failed_operator_comparison_has_finite_json_diagnostics() -> None:
    source = QuantumCircuit(1)
    candidate = QuantumCircuit(1)
    candidate.x(0)
    report = check_operator_equivalence(source, candidate, config=TranspilationConfig())
    assert not report.passed
    assert np.isfinite(report.max_phase_aligned_error)
    # Strict JSON consumers reject the Infinity previously emitted for this case.
    json.dumps(report.to_dict(), allow_nan=False)


def test_contract_and_transpilation_have_explicit_phase_policies() -> None:
    source = build_bell_circuit()
    candidate = source.copy()
    candidate.global_phase = np.pi
    report = verify_contract(candidate, bell_contract())
    state_check = next(check for check in report.checks if check.name == "target-state")
    assert not state_check.passed
    assert state_check.data["equivalent_up_to_global_phase"]
    assert not state_check.data["amplitudes_match"]
    # Operator evidence deliberately has a weaker, phase-insensitive policy.
    assert check_operator_equivalence(
        source, candidate, config=TranspilationConfig(),
    ).passed


@pytest.mark.parametrize("gate,targets,controls", [
    ("H", (0,), ()), (GateName.H, (0,), (1,)),
    (GateName.CNOT, (0,), (0,)), (GateName.SWAP, (0,), ()),
    (GateName.X, (True,), ()), (GateName.X, [0], ()),
])
def test_direct_checked_operation_cannot_bypass_validation(
    gate: object, targets: object, controls: object,
) -> None:
    with pytest.raises(ValueError):
        CheckedOperation(gate, targets, controls)


def test_direct_checked_circuit_checks_register_bounds() -> None:
    operation = CheckedOperation(GateName.H, (2,))
    with pytest.raises(ValueError, match="outside"):
        CheckedCircuitIr("0.1", "invalid", 2, (operation,))


@pytest.mark.parametrize("name,module_name", [
    ("bell", "GeneratedBell"),
    ("ghz3", "GeneratedGhz3"),
    ("dj2_constant", "GeneratedDj2Constant"),
    ("dj2_balanced", "GeneratedDj2Balanced"),
])
def test_committed_lean_is_reproducible(name: str, module_name: str, tmp_path: Path) -> None:
    ir = json.loads((PROJECT_ROOT / f"examples/{name}_ir.json").read_text())
    data = json.loads((PROJECT_ROOT / f"src/fqv/data/{name}.contract.json").read_text())
    generated = generate_lean_module(ir, data)
    committed = PROJECT_ROOT / f"lean/QuantumValidation/{module_name}.lean"
    assert generated.source == committed.read_text(encoding="utf-8")
    output = write_lean_module(ir, data, tmp_path / "Generated.lean")
    # Canonical LF output must also hold on Windows, independently of Git settings.
    assert output.read_bytes() == generated.source.encode("utf-8")


def test_failed_generation_does_not_create_output_directory(tmp_path: Path) -> None:
    data = _contract()
    data["initial_state"] = ["zero"] * 4
    destination = tmp_path / "not-created" / "Invalid.lean"
    with pytest.raises(InvalidContractError, match="normalized"):
        write_lean_module(circuit_to_ir(build_bell_circuit()), data, destination)
    assert not destination.parent.exists()
