"""Exact amplitude vocabulary shared by contracts and formal backends."""

from __future__ import annotations

from enum import StrEnum
from math import sqrt


class AmplitudeToken(StrEnum):
    """Amplitude values admitted by contract schema version 0.1."""

    ZERO = "zero"
    ONE = "one"
    MINUS_ONE = "minus_one"
    I = "i"
    MINUS_I = "minus_i"
    INV_SQRT_TWO = "inv_sqrt_two"
    MINUS_INV_SQRT_TWO = "minus_inv_sqrt_two"


_AMPLITUDE_VALUES: dict[AmplitudeToken, complex] = {
    AmplitudeToken.ZERO: 0.0,
    AmplitudeToken.ONE: 1.0,
    AmplitudeToken.MINUS_ONE: -1.0,
    AmplitudeToken.I: 1.0j,
    AmplitudeToken.MINUS_I: -1.0j,
    AmplitudeToken.INV_SQRT_TWO: 1.0 / sqrt(2.0),
    AmplitudeToken.MINUS_INV_SQRT_TWO: -1.0 / sqrt(2.0),
}


def decode_amplitude(token: str) -> complex:
    """Decode one schema token without introducing parser dependencies."""

    return _AMPLITUDE_VALUES[AmplitudeToken(token)]
