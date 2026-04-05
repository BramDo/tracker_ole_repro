from __future__ import annotations

import numpy as np

from tracker_ole_repro.estimator.definitions import ObservableSpec
from tracker_ole_repro.estimator.ole_estimator import (
    estimate_f_delta,
    estimate_f_delta_monte_carlo,
    evaluate_observable_from_statevector,
    prepare_basis_state,
)


def test_prepare_basis_state_uses_qiskit_compatible_little_endian_indexing() -> None:
    state = prepare_basis_state((1, 0, 1))

    assert state.shape == (8,)
    assert np.isclose(state[5], 1.0)
    assert np.count_nonzero(state) == 1


def test_evaluate_pauli_y_expectation_for_phase_state() -> None:
    state = np.array([1.0, 1.0j], dtype=np.complex128) / np.sqrt(2.0)
    observable = ObservableSpec(label="Y", qubits=(0,))

    expectation = evaluate_observable_from_statevector(state, observable)

    assert np.isclose(expectation, 1.0)


def test_exact_basis_average_respects_estimator_semantics() -> None:
    hadamard = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2.0)
    observable = ObservableSpec(label="X", qubits=(0,))

    result = estimate_f_delta(1, hadamard, observable)

    assert result.exact is True
    assert result.sample_count == 2
    assert np.isclose(result.estimate, 0.0)
    assert np.isclose(result.standard_error, 0.0)


def test_monte_carlo_estimate_converges_on_small_problem() -> None:
    identity = np.eye(4, dtype=np.complex128)
    observable = ObservableSpec(label="Z", qubits=(0,))

    exact = estimate_f_delta(2, identity, observable)
    sampled = estimate_f_delta_monte_carlo(
        2,
        identity,
        observable,
        num_samples=4000,
        random_seed=7,
    )

    assert np.isclose(exact.estimate, 0.0)
    assert sampled.exact is False
    assert abs(sampled.estimate - exact.estimate) < 0.05
    assert sampled.standard_error > 0.0
    assert sampled.confidence_half_width > 0.0
