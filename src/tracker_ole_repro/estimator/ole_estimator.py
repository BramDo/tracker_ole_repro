"""Small OLE estimator core for semantic validation before large runs."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Callable, Iterable, Sequence

import numpy as np
from numpy.typing import NDArray

from .definitions import ObservableSpec

Bitstring = Sequence[int] | str
Evolution = Callable[[NDArray[np.complex128]], NDArray[np.complex128]] | NDArray[np.complex128]

PAULI_MATRICES: dict[str, NDArray[np.complex128]] = {
    "I": np.array([[1, 0], [0, 1]], dtype=np.complex128),
    "X": np.array([[0, 1], [1, 0]], dtype=np.complex128),
    "Y": np.array([[0, -1j], [1j, 0]], dtype=np.complex128),
    "Z": np.array([[1, 0], [0, -1]], dtype=np.complex128),
}


@dataclass(frozen=True, slots=True)
class EstimateResult:
    """Result bundle for exact or Monte Carlo OLE estimation."""

    estimate: float
    standard_error: float
    confidence_half_width: float
    sample_count: int
    exact: bool


def prepare_basis_state(bitstring: Bitstring) -> NDArray[np.complex128]:
    """Return the computational-basis statevector for a qubit-ordered bitstring.

    The sequence position is the qubit index, so `(1, 0, 1)` means qubits
    `q0=1, q1=0, q2=1`. This matches the internal little-endian indexing used by
    Qiskit-compatible statevectors.
    """

    bits = _normalize_bitstring(bitstring)
    state = np.zeros(2 ** len(bits), dtype=np.complex128)
    basis_index = sum(bit << qubit_index for qubit_index, bit in enumerate(bits))
    state[basis_index] = 1.0
    return state


def evaluate_observable_from_statevector(
    statevector: NDArray[np.complex128],
    observable: ObservableSpec,
    *,
    n_qubits: int | None = None,
) -> float:
    """Evaluate a product-Pauli observable on a statevector."""

    statevector = np.asarray(statevector, dtype=np.complex128)
    inferred_qubits = _infer_qubit_count(statevector, n_qubits)
    operator = _build_full_observable_matrix(inferred_qubits, observable)
    expectation = np.vdot(statevector, operator @ statevector)
    return float(np.real_if_close(expectation, tol=1_000))


def estimate_f_delta(
    n_qubits: int,
    evolution: Evolution,
    observable: ObservableSpec,
    *,
    basis_states: Iterable[Bitstring] | None = None,
) -> EstimateResult:
    """Average the observable exactly over the provided or full basis-state set."""

    selected_states = list(basis_states) if basis_states is not None else list(product((0, 1), repeat=n_qubits))
    values = [
        evaluate_observable_from_statevector(
            _apply_evolution(evolution, prepare_basis_state(bitstring)),
            observable,
            n_qubits=n_qubits,
        )
        for bitstring in selected_states
    ]
    estimate = float(np.mean(values)) if values else 0.0
    return EstimateResult(
        estimate=estimate,
        standard_error=0.0,
        confidence_half_width=0.0,
        sample_count=len(values),
        exact=True,
    )


def estimate_f_delta_monte_carlo(
    n_qubits: int,
    evolution: Evolution,
    observable: ObservableSpec,
    *,
    num_samples: int,
    random_seed: int,
) -> EstimateResult:
    """Estimate the benchmark by uniform basis-state sampling."""

    if num_samples <= 0:
        raise ValueError("num_samples must be positive.")

    rng = np.random.default_rng(random_seed)
    samples = rng.integers(0, 2, size=(num_samples, n_qubits), endpoint=False)
    values = np.array(
        [
            evaluate_observable_from_statevector(
                _apply_evolution(evolution, prepare_basis_state(sample.tolist())),
                observable,
                n_qubits=n_qubits,
            )
            for sample in samples
        ],
        dtype=np.float64,
    )

    estimate = float(values.mean())
    standard_error = float(values.std(ddof=1) / np.sqrt(num_samples)) if num_samples > 1 else 0.0
    confidence_half_width = 1.96 * standard_error
    return EstimateResult(
        estimate=estimate,
        standard_error=standard_error,
        confidence_half_width=confidence_half_width,
        sample_count=num_samples,
        exact=False,
    )


def _apply_evolution(
    evolution: Evolution,
    statevector: NDArray[np.complex128],
) -> NDArray[np.complex128]:
    evolved = evolution(statevector) if callable(evolution) else np.asarray(evolution) @ statevector
    return np.asarray(evolved, dtype=np.complex128)


def _build_full_observable_matrix(
    n_qubits: int,
    observable: ObservableSpec,
) -> NDArray[np.complex128]:
    operators_by_qubit = {qubit: PAULI_MATRICES["I"] for qubit in range(n_qubits)}
    for symbol, qubit in zip(observable.label, observable.qubits, strict=True):
        operators_by_qubit[qubit] = PAULI_MATRICES[symbol]

    full_operator = np.array([[1]], dtype=np.complex128)
    for qubit in reversed(range(n_qubits)):
        full_operator = np.kron(full_operator, operators_by_qubit[qubit])
    return full_operator


def _infer_qubit_count(statevector: NDArray[np.complex128], n_qubits: int | None) -> int:
    if n_qubits is not None:
        expected_length = 2 ** n_qubits
        if expected_length != statevector.shape[0]:
            raise ValueError("Statevector length does not match n_qubits.")
        return n_qubits

    log_dim = np.log2(statevector.shape[0])
    if not float(log_dim).is_integer():
        raise ValueError("Statevector length must be a power of two.")
    return int(log_dim)


def _normalize_bitstring(bitstring: Bitstring) -> tuple[int, ...]:
    if isinstance(bitstring, str):
        bits = tuple(int(character) for character in bitstring)
    else:
        bits = tuple(int(bit) for bit in bitstring)

    if any(bit not in (0, 1) for bit in bits):
        raise ValueError("Bitstrings may only contain 0 and 1.")
    return bits


# TODO(tracker-metadata): add tracker-specific helpers for constructing the
# delta-dependent evolution `V_delta`, estimator logging payloads, and the exact
# reference normalization used by tracker raw/rescaled/mitigated outputs.
