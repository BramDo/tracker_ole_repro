"""Tracker-specific basis-term runners against the published QASM circuits."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.quantum_info import SparsePauliOp

from tracker_ole_repro.estimator.validation import compute_z_basis_parity
from tracker_ole_repro.tracker_io.load_qasm import load_tracker_qasm_circuit
from tracker_ole_repro.tracker_io.load_tracker_instance import TrackerInstanceContext, load_tracker_instance


@dataclass(frozen=True, slots=True)
class TrackerBasisTermResult:
    """One tracker basis-state contribution to the OLE estimator."""

    instance_id: str
    simulator_method: str
    input_bitstring: str
    input_sigma: int
    output_expectation: float
    weighted_term: float
    active_qubits: int
    observable_active: tuple[int, ...]
    perturbation_support_active: tuple[int, ...]


def compress_tracker_circuit_to_active_register(context: TrackerInstanceContext) -> QuantumCircuit:
    """Drop idle declared qubits and keep only the active tracker register."""

    full_circuit = load_tracker_qasm_circuit(context.asset.instance_id)
    mapping = {declared_qubit: active_index for active_index, declared_qubit in enumerate(context.qasm_stats.active_qubit_indices)}
    compact_circuit = QuantumCircuit(context.qasm_stats.active_qubits)

    for instruction in full_circuit.data:
        if instruction.operation.name == "barrier":
            continue
        declared_qubits = [full_circuit.find_bit(qubit).index for qubit in instruction.qubits]
        if not declared_qubits:
            continue
        try:
            active_qubits = [compact_circuit.qubits[mapping[declared_qubit]] for declared_qubit in declared_qubits]
        except KeyError as error:
            raise ValueError(f"Encountered non-active qubit {error.args[0]} in tracker circuit.") from error
        compact_circuit.append(instruction.operation, active_qubits, [])
    return compact_circuit


def run_tracker_basis_term(
    instance_id: str,
    bitstring: Sequence[int] | str,
    *,
    simulator_method: str = "matrix_product_state",
) -> TrackerBasisTermResult:
    """Run one published tracker circuit for one basis-state contribution."""

    context = load_tracker_instance(instance_id)
    active_circuit = compress_tracker_circuit_to_active_register(context)
    normalized_bitstring = _normalize_bitstring(bitstring, expected_length=context.qasm_stats.active_qubits)

    circuit = QuantumCircuit(context.qasm_stats.active_qubits)
    for qubit_index, bit in enumerate(normalized_bitstring):
        if bit:
            circuit.x(qubit_index)
    circuit.compose(active_circuit, inplace=True)
    circuit.save_expectation_value(
        SparsePauliOp.from_sparse_list(
            [(context.observable_active.label, list(context.observable_active.qubits), 1.0)],
            num_qubits=context.qasm_stats.active_qubits,
        ),
        list(range(context.qasm_stats.active_qubits)),
        label="observable_expectation",
    )

    result = AerSimulator(method=simulator_method).run(circuit).result()
    output_expectation = float(result.data(0)["observable_expectation"])
    input_sigma = compute_z_basis_parity(normalized_bitstring, context.observable_active)
    return TrackerBasisTermResult(
        instance_id=instance_id,
        simulator_method=simulator_method,
        input_bitstring="".join(str(bit) for bit in normalized_bitstring),
        input_sigma=input_sigma,
        output_expectation=output_expectation,
        weighted_term=input_sigma * output_expectation,
        active_qubits=context.qasm_stats.active_qubits,
        observable_active=context.observable_active.qubits,
        perturbation_support_active=context.perturbation_support_active,
    )


def _normalize_bitstring(bitstring: Sequence[int] | str, *, expected_length: int) -> tuple[int, ...]:
    if isinstance(bitstring, str):
        bits = tuple(int(character) for character in bitstring)
    else:
        bits = tuple(int(bit) for bit in bitstring)
    if len(bits) != expected_length:
        raise ValueError(f"Expected a bitstring of length {expected_length}, got {len(bits)}.")
    if any(bit not in (0, 1) for bit in bits):
        raise ValueError("Bitstrings may only contain 0 and 1.")
    return bits
