from __future__ import annotations

import numpy as np
from pathlib import Path
from qiskit import QuantumCircuit

from tracker_ole_repro.estimator.definitions import ObservableSpec
from tracker_ole_repro.simulation.exact_runner import exact_basis_average, estimate_basis_term, evolve_basis_state
from tracker_ole_repro.tracker_io.load_qasm import load_qasm_circuit


def test_load_qasm_circuit_supports_openqasm3() -> None:
    project_root = Path(__file__).resolve().parents[1]
    scratch_dir = project_root / ".test_artifacts"
    scratch_dir.mkdir(exist_ok=True)
    qasm_path = scratch_dir / "simple-openqasm3.qasm"
    qasm_path.write_text(
        """OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
h q[0];
cz q[0], q[1];
""",
        encoding="utf-8",
    )

    circuit = load_qasm_circuit(qasm_path)

    assert circuit.num_qubits == 2
    assert circuit.depth() == 2


def test_exact_runner_evolves_basis_state_and_evaluates_observable() -> None:
    circuit = QuantumCircuit(2)
    circuit.x(1)
    observable = ObservableSpec(label="Z", qubits=(1,))

    statevector = evolve_basis_state(circuit, (0, 0))
    basis_term = estimate_basis_term(circuit, (0, 0), observable)

    assert np.isclose(np.abs(statevector[2]), 1.0)
    assert np.isclose(basis_term, -1.0)


def test_exact_basis_average_matches_zero_for_balanced_single_qubit_x_rotation() -> None:
    circuit = QuantumCircuit(1)
    circuit.h(0)
    observable = ObservableSpec(label="X", qubits=(0,))

    result = exact_basis_average(circuit, observable)

    assert np.isclose(result.estimate, 0.0)
    assert result.sample_count == 2
