"""Load canonical tracker assets into estimator-facing metadata objects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Sequence

from tracker_ole_repro.circuits.inspect_qasm import QasmInspectionResult, inspect_qasm_path
from tracker_ole_repro.estimator.definitions import BasisSamplingSpec, OLEInstance, ObservableSpec
from tracker_ole_repro.paths import TRACKER_METADATA_DIR, TRACKER_QASM_DIR

from .fetch_tracker_assets import TRACKER_ASSETS, TrackerAssetDefinition

OBSERVABLE_TERM_PATTERN = re.compile(r"([IXYZ])\s*(\d+)")


@dataclass(frozen=True, slots=True)
class TrackerInstanceContext:
    """Combined view of one canonical tracker instance and its observable mapping."""

    asset: TrackerAssetDefinition
    qasm_path: Path
    qasm_stats: QasmInspectionResult
    observable_declared: ObservableSpec
    observable_active: ObservableSpec
    perturbation_support_declared: tuple[int, ...]
    perturbation_support_active: tuple[int, ...]
    ole_instance: OLEInstance


def get_tracker_asset_definition(instance_id: str) -> TrackerAssetDefinition:
    """Return the canonical tracker asset definition for one instance id."""

    for asset in TRACKER_ASSETS:
        if asset.instance_id == instance_id:
            return asset
    raise KeyError(f"Unknown tracker instance id: {instance_id}")


def list_tracker_asset_definitions() -> tuple[TrackerAssetDefinition, ...]:
    """Return the canonical tracker asset catalog."""

    return TRACKER_ASSETS


def parse_tracker_observable(observable_text: str) -> ObservableSpec:
    """Parse tracker observable text like `Z52 Z59 Z72` into an ObservableSpec."""

    terms = OBSERVABLE_TERM_PATTERN.findall(observable_text)
    if not terms:
        raise ValueError(f"Could not parse tracker observable: {observable_text!r}")
    label = "".join(symbol for symbol, _ in terms)
    qubits = tuple(int(index_text) for _, index_text in terms)
    return ObservableSpec(label=label, qubits=qubits)


def remap_observable_to_active_qubits(
    observable: ObservableSpec,
    active_qubit_indices: Sequence[int],
) -> ObservableSpec:
    """Map declared-register observable indices onto compact active-qubit indices."""

    active_lookup = {declared_qubit: active_index for active_index, declared_qubit in enumerate(active_qubit_indices)}
    try:
        remapped_qubits = tuple(active_lookup[declared_qubit] for declared_qubit in observable.qubits)
    except KeyError as error:
        raise ValueError(f"Observable qubit {error.args[0]} is not active in this circuit.") from error
    return ObservableSpec(label=observable.label, qubits=remapped_qubits)


def load_tracker_instance(instance_id: str) -> TrackerInstanceContext:
    """Load one canonical tracker instance into an estimator-facing context object."""

    asset = get_tracker_asset_definition(instance_id)
    qasm_path = TRACKER_QASM_DIR / asset.file_name
    if not qasm_path.exists():
        raise FileNotFoundError(f"Missing tracker QASM asset: {qasm_path}")

    qasm_stats = inspect_qasm_path(qasm_path, instance_id=instance_id)
    observable_declared = parse_tracker_observable(asset.observable)
    observable_active = remap_observable_to_active_qubits(observable_declared, qasm_stats.active_qubit_indices)
    perturbation_support_declared = infer_perturbation_support_declared(qasm_path, delta=asset.delta)
    perturbation_support_active = remap_declared_qubits_to_active_qubits(
        perturbation_support_declared,
        qasm_stats.active_qubit_indices,
    )
    ole_instance = OLEInstance(
        instance_id=asset.instance_id,
        n_active=qasm_stats.active_qubits,
        delta=asset.delta,
        trotter_L=asset.trotter_L,
        observable=observable_active,
        perturbation_support=perturbation_support_active,
        basis_sampling=BasisSamplingSpec(strategy="exact"),
        raw_qasm_path=qasm_path.as_posix(),
        metadata_source=(TRACKER_METADATA_DIR / f"{asset.instance_id}.json").as_posix(),
        perturbation_source="inferred from published QASM as the declared qubits carrying rz(2*delta)",
        notes=(
            f"Declared observable qubits {observable_declared.qubits} remapped onto "
            f"active indices {observable_active.qubits}; inferred perturbation support "
            f"{perturbation_support_declared} remapped to {perturbation_support_active}. "
            "Override basis_sampling with an explicit Monte Carlo policy when running large instances."
        ),
    )
    return TrackerInstanceContext(
        asset=asset,
        qasm_path=qasm_path,
        qasm_stats=qasm_stats,
        observable_declared=observable_declared,
        observable_active=observable_active,
        perturbation_support_declared=perturbation_support_declared,
        perturbation_support_active=perturbation_support_active,
        ole_instance=ole_instance,
    )


def infer_perturbation_support_declared(qasm_path: str | Path, *, delta: float, tolerance: float = 1e-9) -> tuple[int, ...]:
    """Infer perturbation support from the published QASM by locating rz(2*delta)."""

    from .load_qasm import load_qasm_circuit

    circuit = load_qasm_circuit(qasm_path)
    target_angle = 2.0 * delta
    support: list[int] = []
    for instruction in circuit.data:
        if instruction.operation.name != "rz":
            continue
        if len(instruction.operation.params) != 1:
            continue
        angle = float(instruction.operation.params[0])
        if abs(angle - target_angle) > tolerance:
            continue
        declared_qubit = circuit.find_bit(instruction.qubits[0]).index
        support.append(declared_qubit)
    return tuple(sorted(set(support)))


def remap_declared_qubits_to_active_qubits(
    declared_qubits: Sequence[int],
    active_qubit_indices: Sequence[int],
) -> tuple[int, ...]:
    """Map declared qubit ids onto compact active-register positions."""

    active_lookup = {declared_qubit: active_index for active_index, declared_qubit in enumerate(active_qubit_indices)}
    try:
        return tuple(active_lookup[declared_qubit] for declared_qubit in declared_qubits)
    except KeyError as error:
        raise ValueError(f"Declared qubit {error.args[0]} is not active in this circuit.") from error
