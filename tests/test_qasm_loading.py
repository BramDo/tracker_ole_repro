from __future__ import annotations

import csv
from pathlib import Path

from tracker_ole_repro.circuits.inspect_qasm import inspect_qasm_path, inspect_qasm_text, write_qasm_stats_csv


SAMPLE_QASM = """OPENQASM 2.0;
include "qelib1.inc";
qreg q[4];
creg c[2];
// observable qubits: [1, 3]
h q[0];
cx q[0], q[1];
cz q[1], q[3];
rz(0.25) q[3];
measure q[0] -> c[0];
measure q[3] -> c[1];
"""

QASM3_WITH_CUSTOM_GATE = """OPENQASM 3.0;
include "stdgates.inc";
gate flip a {
  x a;
}
qubit[2] q;
flip q[0];
cz q[0], q[1];
"""


def test_inspect_qasm_text_reports_expected_structural_stats() -> None:
    result = inspect_qasm_text(SAMPLE_QASM, instance_id="sample", file_name="sample.qasm")

    assert result.instance_id == "sample"
    assert result.file_name == "sample.qasm"
    assert result.declared_qubits == 4
    assert result.active_qubits == 3
    assert result.active_qubit_indices == (0, 1, 3)
    assert result.total_gate_count == 4
    assert result.cz_count == 1
    assert result.measure_count == 2
    assert result.depth == 5
    assert result.gate_counts == {"cx": 1, "cz": 1, "h": 1, "rz": 1}
    assert result.observable_hints == (1, 3)


def test_inspect_qasm_path_and_csv_export() -> None:
    project_root = Path(__file__).resolve().parents[1]
    temp_path = project_root / ".test_artifacts"
    temp_path.mkdir(exist_ok=True)
    qasm_path = temp_path / "sample.qasm"
    qasm_path.write_text(SAMPLE_QASM, encoding="utf-8")

    result = inspect_qasm_path(qasm_path, instance_id="path-sample")
    output_path = write_qasm_stats_csv([result], temp_path / "qasm_stats.csv")

    with output_path.open("r", encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))

    assert row["instance_id"] == "path-sample"
    assert row["file_name"] == "sample.qasm"
    assert row["active_qubits"] == "3"
    assert row["total_gate_count"] == "4"
    assert '"cz": 1' in row["gate_summary_json"]


def test_qasm3_custom_gate_definition_is_not_counted_as_runtime_gates() -> None:
    result = inspect_qasm_text(QASM3_WITH_CUSTOM_GATE, instance_id="qasm3-custom", file_name="custom.qasm")

    assert result.declared_qubits == 2
    assert result.active_qubits == 2
    assert result.total_gate_count == 2
    assert result.gate_counts == {"cz": 1, "flip": 1}
