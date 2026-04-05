"""Structural inspection utilities for tracker-style OpenQASM files."""

from __future__ import annotations

from dataclasses import dataclass
import csv
import json
from pathlib import Path
import re
from typing import Iterable

QASM2_QREG_PATTERN = re.compile(r"^\s*qreg\s+([A-Za-z_]\w*)\[(\d+)\]\s*;\s*$")
QASM3_QREG_PATTERN = re.compile(r"^\s*qubit\[(\d+)\]\s+([A-Za-z_]\w*)\s*;\s*$")
CREG_PATTERN = re.compile(r"^\s*(?:creg|bit\[\d+\])\s+[A-Za-z_]\w*(?:\[\d+\])?\s*;\s*$")
MEASURE_PATTERN = re.compile(r"^\s*measure\s+(.+?)\s*->\s*(.+?)\s*;\s*$")
INSTRUCTION_NAME_PATTERN = re.compile(r"^\s*([A-Za-z_]\w*)")
INDEXED_REGISTER_PATTERN = re.compile(r"\b([A-Za-z_]\w*)\[(\d+)\]")
COMMENT_PATTERN = re.compile(r"//(.*)$")
NUMBER_PATTERN = re.compile(r"\d+")


@dataclass(frozen=True, slots=True)
class QasmInspectionResult:
    """Compact structural summary for a QASM circuit."""

    instance_id: str
    file_name: str
    declared_qubits: int
    active_qubits: int
    active_qubit_indices: tuple[int, ...]
    total_gate_count: int
    cz_count: int
    depth: int
    measure_count: int
    gate_counts: dict[str, int]
    observable_hints: tuple[int, ...]

    @property
    def has_measurements(self) -> bool:
        """Return whether the QASM contains any measurements."""

        return self.measure_count > 0

    def to_row(self) -> dict[str, object]:
        """Render the result into a CSV-friendly row."""

        return {
            "instance_id": self.instance_id,
            "file_name": self.file_name,
            "declared_qubits": self.declared_qubits,
            "active_qubits": self.active_qubits,
            "active_qubit_indices_json": json.dumps(self.active_qubit_indices),
            "total_gate_count": self.total_gate_count,
            "cz_count": self.cz_count,
            "depth": self.depth,
            "measure_count": self.measure_count,
            "has_measurements": self.has_measurements,
            "observable_hints_json": json.dumps(self.observable_hints),
            "gate_summary_json": json.dumps(self.gate_counts, sort_keys=True),
        }


def inspect_qasm_path(path: str | Path, *, instance_id: str | None = None) -> QasmInspectionResult:
    """Inspect one QASM file from disk."""

    path = Path(path)
    return inspect_qasm_text(
        path.read_text(encoding="utf-8"),
        instance_id=instance_id or path.stem,
        file_name=path.name,
    )


def inspect_qasm_text(
    qasm_text: str,
    *,
    instance_id: str = "unknown",
    file_name: str = "<memory>",
) -> QasmInspectionResult:
    """Inspect structural facts from a tracker-style OpenQASM string.

    The implementation is deliberately lightweight so parser tests stay runnable
    before Qiskit is installed. Depth is a simple greedy schedule on active
    qubits, which is sufficient for reproducible structural comparisons.
    """

    register_sizes: dict[str, int] = {}
    gate_counts: dict[str, int] = {}
    active_qubits: set[int] = set()
    observable_hints: set[int] = set()
    qubit_depths: dict[int, int] = {}
    declared_qubits = 0
    measure_count = 0
    max_depth = 0
    inside_gate_definition = False

    for raw_line in qasm_text.splitlines():
        comment_match = COMMENT_PATTERN.search(raw_line)
        if comment_match:
            observable_hints.update(_extract_comment_observable_hints(comment_match.group(1)))

        line = COMMENT_PATTERN.sub("", raw_line).strip()
        if not line or line.startswith(("OPENQASM", "include")):
            continue

        if inside_gate_definition:
            if line == "}":
                inside_gate_definition = False
            continue

        qasm2_match = QASM2_QREG_PATTERN.match(line)
        if qasm2_match:
            register_name, size_text = qasm2_match.groups()
            size = int(size_text)
            register_sizes[register_name] = size
            declared_qubits = max(declared_qubits, size)
            continue

        qasm3_match = QASM3_QREG_PATTERN.match(line)
        if qasm3_match:
            size_text, register_name = qasm3_match.groups()
            size = int(size_text)
            register_sizes[register_name] = size
            declared_qubits = max(declared_qubits, size)
            continue

        if CREG_PATTERN.match(line):
            continue
        if line.startswith(("gate ", "opaque ")):
            inside_gate_definition = "{" in line and "}" not in line
            continue

        measure_match = MEASURE_PATTERN.match(line)
        if measure_match:
            measure_count += 1
            qubit_indices = _extract_qubit_indices(measure_match.group(1), register_sizes)
            active_qubits.update(qubit_indices)
            max_depth = _schedule_layer(qubit_indices, qubit_depths, max_depth)
            continue

        instruction_match = INSTRUCTION_NAME_PATTERN.match(line)
        if not instruction_match:
            continue

        instruction_name = instruction_match.group(1).lower()
        if instruction_name == "barrier":
            continue

        qubit_indices = _extract_qubit_indices(line, register_sizes)
        active_qubits.update(qubit_indices)
        gate_counts[instruction_name] = gate_counts.get(instruction_name, 0) + 1
        max_depth = _schedule_layer(qubit_indices, qubit_depths, max_depth)

    active_qubit_indices = tuple(sorted(active_qubits))
    return QasmInspectionResult(
        instance_id=instance_id,
        file_name=file_name,
        declared_qubits=declared_qubits,
        active_qubits=len(active_qubit_indices),
        active_qubit_indices=active_qubit_indices,
        total_gate_count=sum(gate_counts.values()),
        cz_count=gate_counts.get("cz", 0),
        depth=max_depth,
        measure_count=measure_count,
        gate_counts=dict(sorted(gate_counts.items())),
        observable_hints=tuple(sorted(observable_hints)),
    )


def write_qasm_stats_csv(results: Iterable[QasmInspectionResult], output_path: str | Path) -> Path:
    """Write a list of inspection results to a CSV file."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [result.to_row() for result in results]
    fieldnames = [
        "instance_id",
        "file_name",
        "declared_qubits",
        "active_qubits",
        "active_qubit_indices_json",
        "total_gate_count",
        "cz_count",
        "depth",
        "measure_count",
        "has_measurements",
        "observable_hints_json",
        "gate_summary_json",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def _extract_comment_observable_hints(comment_text: str) -> set[int]:
    if "observable" not in comment_text.lower():
        return set()
    return {int(match) for match in NUMBER_PATTERN.findall(comment_text)}


def _extract_qubit_indices(text: str, register_sizes: dict[str, int]) -> tuple[int, ...]:
    matches = [
        int(index_text)
        for register_name, index_text in INDEXED_REGISTER_PATTERN.findall(text)
        if register_name in register_sizes
    ]
    if matches:
        return tuple(sorted(set(matches)))

    tokens = {
        token.strip(" ,;")
        for token in re.split(r"[\s,]+", text)
        if token.strip(" ,;")
    }
    expanded: list[int] = []
    for register_name, size in register_sizes.items():
        if register_name in tokens:
            expanded.extend(range(size))
    return tuple(sorted(set(expanded)))


def _schedule_layer(
    qubit_indices: tuple[int, ...],
    qubit_depths: dict[int, int],
    current_max_depth: int,
) -> int:
    if not qubit_indices:
        return current_max_depth

    next_depth = max(qubit_depths.get(qubit_index, 0) for qubit_index in qubit_indices) + 1
    for qubit_index in qubit_indices:
        qubit_depths[qubit_index] = next_depth
    return max(current_max_depth, next_depth)
