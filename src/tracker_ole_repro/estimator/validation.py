"""Validation helpers for tracker-style estimator semantics."""

from __future__ import annotations

from typing import Sequence

from .definitions import ObservableSpec


def compute_z_basis_parity(bitstring: Sequence[int] | str, observable: ObservableSpec) -> int:
    """Return sigma_z for an observable in {I, Z}^{\\otimes n} on one basis state."""

    bits = _normalize_bitstring(bitstring)
    if any(symbol not in {"I", "Z"} for symbol in observable.label):
        raise ValueError("compute_z_basis_parity only supports observables in {I, Z}^{⊗n}.")
    if any(qubit >= len(bits) for qubit in observable.qubits):
        raise ValueError("Observable qubits must fit inside the provided bitstring.")

    parity_exponent = sum(
        bits[qubit]
        for symbol, qubit in zip(observable.label, observable.qubits, strict=True)
        if symbol == "Z"
    )
    return -1 if parity_exponent % 2 else 1


def _normalize_bitstring(bitstring: Sequence[int] | str) -> tuple[int, ...]:
    if isinstance(bitstring, str):
        bits = tuple(int(character) for character in bitstring)
    else:
        bits = tuple(int(bit) for bit in bitstring)
    if any(bit not in (0, 1) for bit in bits):
        raise ValueError("Bitstrings may only contain 0 and 1.")
    return bits
