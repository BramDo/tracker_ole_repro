from __future__ import annotations

import pytest
from qiskit import QuantumCircuit

from tracker_ole_repro.simulation.tracker_hardware_runner import (
    build_tracker_measurement_circuit,
    counts_to_z_observable_expectation,
    generate_smoke_test_bitstrings,
    parse_initial_layout,
    summarize_weighted_terms,
)


def test_counts_to_z_observable_expectation_returns_weighted_parity_average() -> None:
    counts = {"000": 30, "011": 10, "101": 6, "111": 4}

    expectation = counts_to_z_observable_expectation(counts, measured_bits=3)

    assert expectation == pytest.approx((30 + 10 + 6 - 4) / 50)


def test_build_tracker_measurement_circuit_prepares_basis_state_and_measures_observable_support() -> None:
    active_circuit = QuantumCircuit(3)
    active_circuit.cz(0, 1)
    active_circuit.x(2)

    circuit = build_tracker_measurement_circuit(active_circuit, observable_qubits=(0, 2), bitstring="101")

    assert circuit.num_qubits == 3
    assert circuit.num_clbits == 2
    leading_x_targets = [
        circuit.find_bit(instruction.qubits[0]).index
        for instruction in circuit.data
        if instruction.operation.name == "x"
    ]
    assert leading_x_targets[:2] == [0, 2]
    assert circuit.data[-2].operation.name == "measure"
    assert circuit.data[-1].operation.name == "measure"


def test_parse_initial_layout_supports_ranges_and_csv() -> None:
    assert parse_initial_layout("") is None
    assert parse_initial_layout("3,5,7") == (3, 5, 7)
    assert parse_initial_layout("10-12,20") == (10, 11, 12, 20)


def test_generate_smoke_test_bitstrings_is_reproducible_and_includes_zero_state() -> None:
    bitstrings = generate_smoke_test_bitstrings(n_active=5, sample_count=4, random_seed=123)

    assert bitstrings[0] == "00000"
    assert len(bitstrings) == 4
    assert len(set(bitstrings)) == 4
    assert bitstrings == generate_smoke_test_bitstrings(n_active=5, sample_count=4, random_seed=123)


def test_summarize_weighted_terms_reports_mean_and_standard_error() -> None:
    summary = summarize_weighted_terms([0.5, -0.5, 0.25, 0.25])

    assert summary["mean_weighted_term"] == pytest.approx(0.125)
    assert summary["standard_deviation"] == pytest.approx(0.4330127018922193)
    assert summary["standard_error"] == pytest.approx(0.21650635094610965)
    assert summary["min_weighted_term"] == pytest.approx(-0.5)
    assert summary["max_weighted_term"] == pytest.approx(0.5)
