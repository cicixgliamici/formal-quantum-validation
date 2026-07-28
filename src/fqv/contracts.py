"""Compatibility imports for the pre-refactor contract API."""

from fqv.domain.contract_parser import contract_from_dict, load_contract
from fqv.domain.contract_validation import InvalidContractError
from fqv.domain.contracts import QuantumContract
from fqv.domain.expectations import ProbabilityExpectation

__all__ = [
    "InvalidContractError",
    "ProbabilityExpectation",
    "QuantumContract",
    "contract_from_dict",
    "load_contract",
]
