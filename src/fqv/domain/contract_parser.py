"""Parse raw JSON contracts into validated domain objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from fqv.domain.amplitudes import decode_amplitude
from fqv.domain.contract_validation import (
    InvalidContractError,
    require_mapping,
    require_nonnegative_number,
    require_number_in_unit_interval,
)
from fqv.domain.contracts import QuantumContract
from fqv.domain.expectations import ProbabilityExpectation


def _decode_state(
    tokens: object,
    *,
    field_name: str,
    num_qubits: int,
) -> tuple[complex, ...]:
    """Decode a dimension-checked exact state vector."""

    if not isinstance(tokens, list):
        raise InvalidContractError(f"{field_name} must be a JSON array")

    # A pure n-qubit state has exactly 2^n computational-basis amplitudes.
    # Checking this here prevents a malformed state from entering the domain.
    expected_size = 2 ** num_qubits
    if len(tokens) != expected_size:
        raise InvalidContractError(
            f"{field_name} requires {expected_size} amplitudes, "
            f"observed {len(tokens)}"
        )

    # The schema uses a small symbolic vocabulary so that JSON, Python, and
    # Lean refer to the same exact intended constants.
    amplitudes: list[complex] = []
    for index, token in enumerate(tokens):
        if not isinstance(token, str):
            raise InvalidContractError(
                f"{field_name}[{index}] uses unsupported amplitude {token!r}"
            )
        try:
            amplitudes.append(decode_amplitude(token))
        except ValueError as error:
            raise InvalidContractError(
                f"{field_name}[{index}] uses unsupported amplitude {token!r}"
            ) from error
    return tuple(amplitudes)


def _parse_expectations(
    values: object,
    *,
    num_qubits: int,
) -> tuple[ProbabilityExpectation, ...]:
    """Parse probability expectations and reject duplicates."""

    if not isinstance(values, list):
        raise InvalidContractError("probabilities must be a JSON array")

    # Duplicate outcomes would make a contract ambiguous: two tolerances could
    # independently judge the same observable event.
    expectations: list[ProbabilityExpectation] = []
    outcomes: set[str] = set()
    for index, raw_value in enumerate(values):
        value = require_mapping(
            raw_value,
            field_name=f"probabilities[{index}]",
        )
        outcome = value.get("outcome")
        if (
            not isinstance(outcome, str)
            or len(outcome) != num_qubits
            or any(bit not in "01" for bit in outcome)
        ):
            raise InvalidContractError(
                f"probabilities[{index}].outcome must be a "
                f"{num_qubits}-bit string"
            )
        if outcome in outcomes:
            raise InvalidContractError(
                f"duplicate probability outcome {outcome!r}"
            )
        outcomes.add(outcome)
        expectations.append(
            ProbabilityExpectation(
                outcome=outcome,
                expected=require_number_in_unit_interval(
                    value.get("expected"),
                    field_name=f"probabilities[{index}].expected",
                ),
                exact_tolerance=require_nonnegative_number(
                    value.get("exact_tolerance", 1e-12),
                    field_name=f"probabilities[{index}].exact_tolerance",
                ),
                sampled_tolerance=require_nonnegative_number(
                    value.get("sampled_tolerance", 0.05),
                    field_name=f"probabilities[{index}].sampled_tolerance",
                ),
            )
        )
    return tuple(expectations)


def _parse_gate_counts(resources: Mapping[str, Any]) -> dict[str, int]:
    """Parse logical resource constraints."""

    raw_counts = require_mapping(
        resources.get("gate_counts"),
        field_name="resources.gate_counts",
    )
    counts: dict[str, int] = {}
    for gate_name, count in raw_counts.items():
        if (
            not isinstance(gate_name, str)
            or not isinstance(count, int)
            or isinstance(count, bool)
            or count < 0
        ):
            raise InvalidContractError(
                "gate counts require string keys and "
                "non-negative integer values"
            )
        counts[gate_name] = count
    return counts


def contract_from_dict(data: Mapping[str, Any]) -> QuantumContract:
    """Parse contract schema version 0.1 into the domain model.

    This function validates document shape and field-level invariants. It does
    not execute a circuit and does not decide whether the contract is true.
    Keeping those responsibilities separate makes parser failures distinct
    from verification failures during a presentation or experiment.
    """

    if data.get("schema_version") != "0.1":
        raise InvalidContractError(
            "only contract schema version '0.1' is supported"
        )

    name = data.get("name")
    num_qubits = data.get("qubits")
    if not isinstance(name, str) or not name:
        raise InvalidContractError("name must be a non-empty string")
    if (
        not isinstance(num_qubits, int)
        or isinstance(num_qubits, bool)
        or num_qubits < 1
    ):
        raise InvalidContractError("qubits must be a positive integer")

    resources = require_mapping(
        data.get("resources"),
        field_name="resources",
    )
    allow_extra_gates = resources.get("allow_extra_gates", False)
    if not isinstance(allow_extra_gates, bool):
        raise InvalidContractError(
            "resources.allow_extra_gates must be a boolean"
        )

    # Construction is the trust boundary: after this point callers work with a
    # typed, immutable domain object rather than loosely shaped JSON.
    return QuantumContract(
        name=name,
        num_qubits=num_qubits,
        gate_counts=_parse_gate_counts(resources),
        allow_extra_gates=allow_extra_gates,
        initial_state=_decode_state(
            data.get("initial_state"),
            field_name="initial_state",
            num_qubits=num_qubits,
        ),
        target_state=_decode_state(
            data.get("target_state"),
            field_name="target_state",
            num_qubits=num_qubits,
        ),
        fidelity_threshold=require_number_in_unit_interval(
            data.get("fidelity_threshold"),
            field_name="fidelity_threshold",
        ),
        probabilities=_parse_expectations(
            data.get("probabilities"),
            num_qubits=num_qubits,
        ),
    )


def load_contract(path: str | Path) -> QuantumContract:
    """Perform file I/O, then delegate all interpretation to the parser."""

    contract_path = Path(path)
    raw = json.loads(contract_path.read_text(encoding="utf-8"))
    return contract_from_dict(
        require_mapping(raw, field_name="contract")
    )
