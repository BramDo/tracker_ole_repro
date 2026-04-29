# renamed test file from semantics to definition
from __future__ import annotations

import numpy as np

from tracker_ole_repro.estimator.definitions import ObservableSpec
from tracker_ole_repro.estimator.ole_estimator import (
    estimate_f_delta,
    estimate_f_delta_monte_carlo,
    evaluate_observable_from_statevector,
    prepare_basis_state,
)


def test_prepare_basis_state_definition() -> None:
    state = prepare_basis_state((1, 0, 1))
    assert state.shape == (8,)
    assert np.isclose(state[5], 1.0)


def test_definition_expectation() -> None:
    state = np.array([1.0, 1.0j], dtype=np.complex128) / np.sqrt(2.0)
    observable = ObservableSpec(label="Y", qubits=(0,))
    expectation = evaluate_observable_from_statevector(state, observable)
    assert np.isclose(expectation, 1.0)
