from __future__ import annotations

from pathlib import Path
import os

import pytest

from tracker_ole_repro.simulation.tracker_runner import compress_tracker_circuit_to_active_register, run_tracker_basis_term
from tracker_ole_repro.tracker_io.load_tracker_instance import load_tracker_instance


def test_compress_tracker_circuit_to_active_register_matches_49q_shape() -> None:
    qasm_path = Path("data/raw/tracker_qasm/49Q_OLE_circuit_L_3_b_0.25_delta0.15.qasm")
    if not qasm_path.exists():
        pytest.skip("Canonical tracker assets have not been fetched yet.")

    context = load_tracker_instance("operator_loschmidt_echo_49x648")
    compact = compress_tracker_circuit_to_active_register(context)

    assert compact.num_qubits == 49
    assert compact.size() == 4756
    assert compact.depth() == 149


def test_run_tracker_basis_term_accepts_zero_state_for_49q_instance() -> None:
    qasm_path = Path("data/raw/tracker_qasm/49Q_OLE_circuit_L_3_b_0.25_delta0.15.qasm")
    if not qasm_path.exists():
        pytest.skip("Canonical tracker assets have not been fetched yet.")
    if os.environ.get("TRACKER_RUN_FULL_SIM") != "1":
        pytest.skip("Set TRACKER_RUN_FULL_SIM=1 to run the expensive 49Q tracker simulation probe.")

    result = run_tracker_basis_term(
        "operator_loschmidt_echo_49x648",
        "0" * 49,
        simulator_method="matrix_product_state",
    )

    assert result.instance_id == "operator_loschmidt_echo_49x648"
    assert result.active_qubits == 49
    assert result.input_sigma == 1
    assert result.observable_active == (33, 39, 45)
    assert result.perturbation_support_active == (
        4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16,
        18, 19, 20, 21, 22, 23, 24, 26, 27, 28, 29, 30,
    )
    assert -1.0 <= result.output_expectation <= 1.0
    assert -1.0 <= result.weighted_term <= 1.0
