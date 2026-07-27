from __future__ import annotations

from dataclasses import dataclass
import json
from math import sqrt
from pathlib import Path
from typing import Any, Mapping, Sequence


class InvalidContractError(ValueError):
    """Raised when a contract cannot be interpreted safely."""


_EXACT_AMPLITUDES: dict[str, complex] = {
    "zero": 0.0,
    "one": 1.0,
    "minus_one": -1.0,
    "i": 1.0j,
    "minus_i": -1.0j,
    "inv_sqrt_two": 1.0 / sqrt(2.0),
    "minus_inv_sqrt_two": -1.0 / sqrt(2.0),
}


@dataclass(frozen=True)
class ProbabilityExpectation:
    """Expected probability for one computational-basis outcome."""

    outcome: str
    expected: float

    # Exact statevector verification tolerance.
    exact_tolerance: float = 1e-12

    # Empirical sampling tolerance.
    sampled_tolerance: float = 0.05


@dataclass(frozen=True)
class QuantumContract:
    """Restricted contract for an ideal unitary quantum circuit."""

    name: str

    # Structural specification.
    num_qubits: int
    gate_counts: Mapping[str, int]
    allow_extra_gates: bool

    # Semantic specification.
    initial_state: Sequence[complex]
    target_state: Sequence[complex]
    fidelity_threshold: float

    # Measurement specification.
    probabilities: tuple[ProbabilityExpectation, ...]


def _require_mapping(
    value: object,
    *,
    field_name: str,
) -> Mapping[str, Any]:
    """Return a mapping or report the field that has the wrong shape."""

    if not isinstance(value, dict):
        raise InvalidContractError(
            f"{field_name} must be a JSON object"
        )

    return value


def _decode_state(
    tokens: object,
    *,
    field_name: str,
    num_qubits: int,
) -> tuple[complex, ...]:
    """Decode exact symbolic amplitudes without losing their intended form."""

    if not isinstance(tokens, list):
        raise InvalidContractError(
            f"{field_name} must be a JSON array"
        )

    expected_size = 2 ** num_qubits
    if len(tokens) != expected_size:
        raise InvalidContractError(
            f"{field_name} requires {expected_size} amplitudes, "
            f"observed {len(tokens)}"
        )

    amplitudes: list[complex] = []
    for index, token in enumerate(tokens):
        if (
            not isinstance(token, str)
            or token not in _EXACT_AMPLITUDES
        ):
            raise InvalidContractError(
                f"{field_name}[{index}] uses unsupported "
                f"amplitude {token!r}"
            )

        amplitudes.append(_EXACT_AMPLITUDES[str(token)])

    return tuple(amplitudes)


def _parse_probabilities(
    values: object,
    *,
    num_qubits: int,
) -> tuple[ProbabilityExpectation, ...]:
    """Parse measurement expectations and reject ambiguous outcomes."""

    if not isinstance(values, list):
        raise InvalidContractError(
            "probabilities must be a JSON array"
        )

    expectations: list[ProbabilityExpectation] = []
    observed_outcomes: set[str] = set()

    for index, raw_value in enumerate(values):
        value = _require_mapping(
            raw_value,
            field_name=f"probabilities[{index}]",
        )
        outcome = value.get("outcome")
        expected = value.get("expected")

        if (
            not isinstance(outcome, str)
            or len(outcome) != num_qubits
            or any(bit not in "01" for bit in outcome)
        ):
            raise InvalidContractError(
                f"probabilities[{index}].outcome must be a "
                f"{num_qubits}-bit string"
            )

        if outcome in observed_outcomes:
            raise InvalidContractError(
                f"duplicate probability outcome {outcome!r}"
            )

        if (
            not isinstance(expected, (int, float))
            or isinstance(expected, bool)
            or not 0.0 <= float(expected) <= 1.0
        ):
            raise InvalidContractError(
                f"probabilities[{index}].expected must be in [0, 1]"
            )

        exact_tolerance = value.get("exact_tolerance", 1e-12)
        sampled_tolerance = value.get(
            "sampled_tolerance",
            0.05,
        )
        for field_name, tolerance in (
            ("exact_tolerance", exact_tolerance),
            ("sampled_tolerance", sampled_tolerance),
        ):
            if (
                not isinstance(tolerance, (int, float))
                or isinstance(tolerance, bool)
                or float(tolerance) < 0.0
            ):
                raise InvalidContractError(
                    f"probabilities[{index}].{field_name} "
                    "must be non-negative"
                )

        observed_outcomes.add(outcome)
        expectations.append(
            ProbabilityExpectation(
                outcome=outcome,
                expected=float(expected),
                exact_tolerance=float(exact_tolerance),
                sampled_tolerance=float(sampled_tolerance),
            )
        )

    return tuple(expectations)


def contract_from_dict(data: Mapping[str, Any]) -> QuantumContract:
    """Interpret contract schema version 0.1 as an executable contract."""

    if data.get("schema_version") != "0.1":
        raise InvalidContractError(
            "only contract schema version '0.1' is supported"
        )

    name = data.get("name")
    num_qubits = data.get("qubits")
    fidelity_threshold = data.get("fidelity_threshold")

    if not isinstance(name, str) or not name:
        raise InvalidContractError("name must be a non-empty string")

    if (
        not isinstance(num_qubits, int)
        or isinstance(num_qubits, bool)
        or num_qubits < 1
    ):
        raise InvalidContractError(
            "qubits must be a positive integer"
        )

    if (
        not isinstance(fidelity_threshold, (int, float))
        or isinstance(fidelity_threshold, bool)
        or not 0.0 <= float(fidelity_threshold) <= 1.0
    ):
        raise InvalidContractError(
            "fidelity_threshold must be in [0, 1]"
        )

    resources = _require_mapping(
        data.get("resources"),
        field_name="resources",
    )
    gate_counts = _require_mapping(
        resources.get("gate_counts"),
        field_name="resources.gate_counts",
    )
    allow_extra_gates = resources.get(
        "allow_extra_gates",
        False,
    )
    if not isinstance(allow_extra_gates, bool):
        raise InvalidContractError(
            "resources.allow_extra_gates must be a boolean"
        )

    parsed_counts: dict[str, int] = {}
    for gate_name, count in gate_counts.items():
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

        parsed_counts[gate_name] = count

    return QuantumContract(
        name=name,
        num_qubits=num_qubits,
        gate_counts=parsed_counts,
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
        fidelity_threshold=float(fidelity_threshold),
        probabilities=_parse_probabilities(
            data.get("probabilities"),
            num_qubits=num_qubits,
        ),
    )


def load_contract(path: str | Path) -> QuantumContract:
    """Load and validate a versioned JSON contract."""

    contract_path = Path(path)
    data = json.loads(contract_path.read_text(encoding="utf-8"))
    mapping = _require_mapping(data, field_name="contract")
    return contract_from_dict(mapping)
