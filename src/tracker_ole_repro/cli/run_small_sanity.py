"""Run a small exact and Monte Carlo sanity check for the local estimator core."""

from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from tracker_ole_repro.estimator.definitions import ObservableSpec
from tracker_ole_repro.estimator.ole_estimator import estimate_f_delta_monte_carlo
from tracker_ole_repro.simulation.exact_runner import exact_basis_average, estimate_basis_term


def main() -> None:
    circuit = QuantumCircuit(3)
    circuit.h(0)
    circuit.cz(0, 1)
    circuit.rx(0.2, 2)

    observable = ObservableSpec(label="X", qubits=(0,))
    exact = exact_basis_average(circuit, observable)
    sampled = estimate_f_delta_monte_carlo(
        3,
        lambda statevector: np.asarray(Statevector(statevector).evolve(circuit).data, dtype=np.complex128),
        observable,
        num_samples=2048,
        random_seed=7,
    )
    term_000 = estimate_basis_term(circuit, (0, 0, 0), observable)
    term_101 = estimate_basis_term(circuit, (1, 0, 1), observable)

    print(f"exact_estimate={exact.estimate}")
    print(f"sampled_estimate={sampled.estimate}")
    print(f"sampled_standard_error={sampled.standard_error}")
    print(f"basis_term_000={term_000}")
    print(f"basis_term_101={term_101}")


if __name__ == "__main__":
    main()
