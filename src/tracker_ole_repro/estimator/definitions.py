"""Core benchmark definitions for tracker-style OLE estimation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True, slots=True)
class ObservableSpec:
    """Product observable on specific qubit indices."""

    label: str
    qubits: tuple[int, ...]

    def __post_init__(self) -> None:
        normalized_label = self.label.upper()
        if len(normalized_label) != len(self.qubits):
            raise ValueError("Observable label length must match the number of qubits.")
        if any(symbol not in {"I", "X", "Y", "Z"} for symbol in normalized_label):
            raise ValueError("Observable label may only use I, X, Y, and Z.")
        object.__setattr__(self, "label", normalized_label)


@dataclass(frozen=True, slots=True)
class BasisSamplingSpec:
    """Sampling policy for computational-basis initial states."""

    strategy: Literal["exact", "monte_carlo"]
    sample_count: int | None = None
    random_seed: int | None = None

    def __post_init__(self) -> None:
        if self.strategy == "exact" and self.sample_count not in (None, 0):
            raise ValueError("Exact sampling does not take a finite sample count.")
        if self.strategy == "monte_carlo" and (self.sample_count is None or self.sample_count <= 0):
            raise ValueError("Monte Carlo sampling requires a positive sample count.")


@dataclass(frozen=True, slots=True)
class OLEInstance:
    """Canonical benchmark description used across parsing, simulation, and analysis."""

    instance_id: str
    n_active: int
    delta: float
    trotter_L: int
    observable: ObservableSpec
    perturbation_support: tuple[int, ...] | None = None
    estimator_type: str = "tracker_fixed_observable"
    basis_sampling: BasisSamplingSpec = field(default_factory=lambda: BasisSamplingSpec(strategy="exact"))
    raw_qasm_path: str | None = None
    metadata_source: str | None = None
    perturbation_source: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.n_active <= 0:
            raise ValueError("n_active must be positive.")
        if self.trotter_L <= 0:
            raise ValueError("trotter_L must be positive.")
        if any(qubit < 0 or qubit >= self.n_active for qubit in self.observable.qubits):
            raise ValueError("Observable qubits must fall inside the active register.")
        if self.perturbation_support is not None and any(
            qubit < 0 or qubit >= self.n_active for qubit in self.perturbation_support
        ):
            raise ValueError("Perturbation support qubits must fall inside the active register.")
        if not self.instance_id:
            raise ValueError("instance_id may not be empty.")

        # TODO(tracker-metadata): replace free-form metadata_source/notes with
        # tracker asset hashes and canonical provenance records once the fetcher
        # and metadata parser are wired in.
