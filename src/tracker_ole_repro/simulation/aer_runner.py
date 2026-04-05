"""Qiskit Aer entry points for local tracker OLE simulation."""

from __future__ import annotations

from typing import Any

import numpy as np

try:
    from qiskit_aer import AerSimulator
except ImportError:  # pragma: no cover - exercised only when Aer is absent.
    AerSimulator = None  # type: ignore[assignment]


def build_aer_simulator(
    *,
    method: str = "statevector",
    seed_simulator: int | None = None,
    max_parallel_threads: int | None = None,
) -> "AerSimulator":
    """Construct a Qiskit Aer simulator using Qiskit 2.1-style imports."""

    if AerSimulator is None:
        raise ImportError("qiskit-aer is required to build an AerSimulator.")

    options: dict[str, Any] = {"method": method}
    if seed_simulator is not None:
        options["seed_simulator"] = seed_simulator
    if max_parallel_threads is not None:
        options["max_parallel_threads"] = max_parallel_threads
    return AerSimulator(**options)


def run_statevector(
    circuit: Any,
    *,
    seed_simulator: int | None = None,
    max_parallel_threads: int | None = None,
) -> np.ndarray:
    """Execute one circuit and return the final statevector as a NumPy array."""

    simulator = build_aer_simulator(
        method="statevector",
        seed_simulator=seed_simulator,
        max_parallel_threads=max_parallel_threads,
    )
    compiled_circuit = circuit.copy()
    compiled_circuit.save_statevector()
    result = simulator.run(compiled_circuit, shots=1).result()
    return np.asarray(result.get_statevector(compiled_circuit), dtype=np.complex128)


# TODO(tracker-metadata): add tracker run manifests that log instance id,
# estimator mode, basis-sample count, delta, and seed information into
# `data/results/` before scaling to 49Q and 70Q runs.
