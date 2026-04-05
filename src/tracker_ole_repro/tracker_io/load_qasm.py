"""Load OpenQASM 2 or 3 circuits into Qiskit QuantumCircuit objects."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qiskit import QuantumCircuit
from qiskit import qasm3

from .load_tracker_instance import get_tracker_asset_definition
from tracker_ole_repro.paths import TRACKER_QASM_DIR


def load_qasm_circuit(path: str | Path) -> QuantumCircuit:
    """Load one QASM file, dispatching between OpenQASM 2 and 3."""

    path = Path(path)
    first_line = path.read_text(encoding="utf-8").splitlines()[0].strip()
    if first_line.startswith("OPENQASM 3"):
        return qasm3.load(str(path))
    return QuantumCircuit.from_qasm_file(str(path))


def load_tracker_qasm_circuit(instance_id: str) -> QuantumCircuit:
    """Load one canonical tracker QASM circuit by instance id."""

    asset = get_tracker_asset_definition(instance_id)
    return load_qasm_circuit(TRACKER_QASM_DIR / asset.file_name)
