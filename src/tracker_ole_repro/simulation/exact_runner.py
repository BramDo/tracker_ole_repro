"""Small exact-statevector helpers for estimator validation on reduced circuits."""

from __future__ import annotations

from typing import Sequence

import numpy as np
from numpy.typing import NDArray
from qiskit.quantum_info import Statevector

from tracker_ole_repro.estimator.definitions import ObservableSpec
from tracker_ole_repro.estimator.ole_estimator import estimate_f_delta, evaluate_observable_from_statevector, prepare_basis_state


def evolve_basis_state(circuit, bitstring: Sequence[int] | str) -> NDArray[np.complex128]:
    """Evolve one computational basis state through a circuit.

    This helper is intended for small validation circuits, not for the full
    49Q/70Q tracker instances.
    """

    initial_state = Statevector(prepare_basis_state(bitstring))
    evolved_state = initial_state.evolve(circuit)
    return np.asarray(evolved_state.data, dtype=np.complex128)


def estimate_basis_term(circuit, bitstring: Sequence[int] | str, observable: ObservableSpec) -> float:
    """Compute one tracker-style term <z_out|O|z_out> for a basis input state."""

    evolved_state = evolve_basis_state(circuit, bitstring)
    return evaluate_observable_from_statevector(
        evolved_state,
        observable,
        n_qubits=circuit.num_qubits,
    )


def exact_basis_average(circuit, observable: ObservableSpec):
    """Average one observable over all computational basis states exactly."""

    return estimate_f_delta(
        circuit.num_qubits,
        lambda statevector: np.asarray(Statevector(statevector).evolve(circuit).data, dtype=np.complex128),
        observable,
    )
