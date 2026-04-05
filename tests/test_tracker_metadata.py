from __future__ import annotations

from pathlib import Path

import pytest

from tracker_ole_repro.estimator.validation import compute_z_basis_parity
from tracker_ole_repro.tracker_io.fetch_tracker_assets import TRACKER_ASSETS
from tracker_ole_repro.tracker_io.load_tracker_instance import (
    infer_perturbation_support_declared,
    load_tracker_instance,
    parse_tracker_observable,
    remap_observable_to_active_qubits,
)


def test_parse_tracker_observable_extracts_label_and_declared_qubits() -> None:
    observable = parse_tracker_observable("Z52 Z59 Z72")

    assert observable.label == "ZZZ"
    assert observable.qubits == (52, 59, 72)


def test_remap_observable_to_active_qubits_matches_canonical_49q_mapping() -> None:
    observable = parse_tracker_observable("Z52 Z59 Z72")
    active_qubit_indices = (
        7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 25, 26, 27, 28, 29, 30, 31, 32,
        33, 34, 35, 37, 38, 39, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 57, 58,
        59, 67, 68, 69, 70, 71, 72, 73, 74, 75,
    )

    remapped = remap_observable_to_active_qubits(observable, active_qubit_indices)

    assert remapped.label == "ZZZ"
    assert remapped.qubits == (33, 39, 45)


def test_compute_z_basis_parity_matches_tracker_sigma_z_convention() -> None:
    observable = parse_tracker_observable("Z0 Z2 Z4")

    assert compute_z_basis_parity((0, 0, 0, 0, 0), observable) == 1
    assert compute_z_basis_parity((1, 0, 0, 0, 0), observable) == -1
    assert compute_z_basis_parity((1, 0, 1, 0, 0), observable) == 1
    assert compute_z_basis_parity((1, 0, 1, 0, 1), observable) == -1


def test_load_tracker_instance_uses_local_fetched_assets_when_available() -> None:
    first_asset = TRACKER_ASSETS[0]
    qasm_path = Path("data/raw/tracker_qasm") / first_asset.file_name
    if not qasm_path.exists():
        pytest.skip("Canonical tracker assets have not been fetched yet.")

    context = load_tracker_instance(first_asset.instance_id)

    assert context.ole_instance.instance_id == first_asset.instance_id
    assert context.ole_instance.n_active == 49
    assert context.observable_declared.qubits == (52, 59, 72)
    assert context.observable_active.qubits == (33, 39, 45)
    assert context.perturbation_support_declared == (
        11, 12, 13, 14, 15, 18, 19, 25, 26, 27, 28, 29,
        31, 32, 33, 34, 35, 37, 38, 45, 46, 47, 48, 49,
    )
    assert context.perturbation_support_active == (
        4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16,
        18, 19, 20, 21, 22, 23, 24, 26, 27, 28, 29, 30,
    )


def test_infer_perturbation_support_declared_from_fetched_49q_asset() -> None:
    qasm_path = Path("data/raw/tracker_qasm/49Q_OLE_circuit_L_3_b_0.25_delta0.15.qasm")
    if not qasm_path.exists():
        pytest.skip("Canonical tracker assets have not been fetched yet.")

    support = infer_perturbation_support_declared(qasm_path, delta=0.15)

    assert support == (
        11, 12, 13, 14, 15, 18, 19, 25, 26, 27, 28, 29,
        31, 32, 33, 34, 35, 37, 38, 45, 46, 47, 48, 49,
    )
