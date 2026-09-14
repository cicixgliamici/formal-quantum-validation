"""Check provenance output and the reviewer-facing negative demonstration."""

from __future__ import annotations

import json
from pathlib import Path

from fqv.domain.reports import CheckResult, VerificationReport
from fqv.evidence_manifest import write_verification_manifest
from fqv.failure_demo import main as failure_demo_main


def test_manifest_hashes_inputs_and_states_proof_boundary(tmp_path: Path) -> None:
    ir_path = tmp_path / "input.json"
    contract_path = tmp_path / "contract.json"
    proof_path = tmp_path / "Generated.lean"
    ir_path.write_text("{}\n", encoding="utf-8")
    contract_path.write_text("{}\n", encoding="utf-8")
    proof_path.write_text("theorem generated : True := by trivial\n", encoding="utf-8")
    report = VerificationReport("example")
    report.add(CheckResult("state", True, "matched"))

    output = write_verification_manifest(
        tmp_path / "manifest.json",
        ir_path=ir_path,
        contract_path=contract_path,
        verification=report,
        proof_path=proof_path,
        proof_backend="lean",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert payload["passed"] is True
    assert len(payload["inputs"]["ir"]["sha256"]) == 64
    assert payload["formal_proof"]["status"] == "generated_not_kernel_checked"
    assert payload["formal_proof"]["backend"] == "lean"


def test_phase_demo_treats_the_expected_rejection_as_success(
    monkeypatch, capsys
) -> None:
    monkeypatch.setattr("sys.argv", ["fqv-demo-phase", "--shots", "4096", "--seed", "7"])

    assert failure_demo_main() == 0
    output = capsys.readouterr().out
    assert "Measurement probabilities: PASS" in output
    assert "Exact quantum state: FAIL" in output
    assert "relative" in output
