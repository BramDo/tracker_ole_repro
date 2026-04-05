"""IBM Runtime helpers for tracker basis-term hardware runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
from pathlib import Path
import statistics
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
import os

import numpy as np
from qiskit import QuantumCircuit, transpile

from tracker_ole_repro.estimator.validation import compute_z_basis_parity
from tracker_ole_repro.paths import HARDWARE_RESULTS_DIR
from tracker_ole_repro.simulation.tracker_runner import compress_tracker_circuit_to_active_register
from tracker_ole_repro.tracker_io.load_tracker_instance import TrackerInstanceContext, load_tracker_instance


@dataclass(frozen=True, slots=True)
class TrackerHardwareConfig:
    """Minimal hardware-run configuration for one tracker basis-term probe."""

    instance_id: str
    bitstring: str
    shots: int
    backend: str | None = None
    optimization_level: int = 1
    seed_transpiler: int | None = None
    initial_layout: tuple[int, ...] | None = None
    reuse_hardware_job_id: str | None = None
    submit_only: bool = False


@dataclass(frozen=True, slots=True)
class TrackerHardwareSmokeConfig:
    """Configuration for a small multi-circuit hardware smoke test."""

    instance_id: str
    sample_count: int
    shots: int
    random_seed: int
    backend: str | None = None
    optimization_level: int = 1
    seed_transpiler: int | None = None
    initial_layout: tuple[int, ...] | None = None
    bitstrings: tuple[str, ...] | None = None


def build_tracker_measurement_circuit(
    active_circuit: QuantumCircuit,
    observable_qubits: Sequence[int],
    bitstring: Sequence[int] | str,
) -> QuantumCircuit:
    """Prepare one basis state, run the active tracker circuit, and measure O-support qubits."""

    normalized_bits = _normalize_bitstring(bitstring, expected_length=active_circuit.num_qubits)
    circuit = QuantumCircuit(active_circuit.num_qubits, len(observable_qubits))
    for qubit_index, bit in enumerate(normalized_bits):
        if bit == "1":
            circuit.x(qubit_index)
    circuit.compose(active_circuit, inplace=True)
    for classical_index, qubit_index in enumerate(observable_qubits):
        circuit.measure(qubit_index, classical_index)
    return circuit


def counts_to_z_observable_expectation(counts: Mapping[Any, Any], measured_bits: int) -> float:
    """Estimate the Z-product expectation value from computational-basis counts."""

    normalized_counts = _normalize_counts(counts, num_bits=measured_bits)
    total = float(sum(normalized_counts.values()))
    if total <= 0.0:
        raise ValueError("Counts are empty; cannot estimate expectation.")

    expectation = 0.0
    for bitstring, count in normalized_counts.items():
        parity = -1.0 if bitstring.count("1") % 2 else 1.0
        expectation += parity * (float(count) / total)
    return expectation


def generate_smoke_test_bitstrings(
    *,
    n_active: int,
    sample_count: int,
    random_seed: int,
) -> tuple[str, ...]:
    """Generate a reproducible small set of unique basis states for smoke tests."""

    if n_active <= 0:
        raise ValueError("n_active must be positive.")
    if sample_count <= 0:
        raise ValueError("sample_count must be positive.")

    zero_state = "0" * n_active
    if sample_count == 1:
        return (zero_state,)

    rng = np.random.default_rng(random_seed)
    bitstrings = [zero_state]
    seen = {zero_state}
    while len(bitstrings) < sample_count:
        candidate = "".join(str(int(bit)) for bit in rng.integers(0, 2, size=n_active))
        if candidate in seen:
            continue
        seen.add(candidate)
        bitstrings.append(candidate)
    return tuple(bitstrings)


def summarize_weighted_terms(weighted_terms: Sequence[float]) -> dict[str, float]:
    """Return a compact aggregate summary for a small basis-term sample."""

    values = [float(value) for value in weighted_terms]
    if not values:
        raise ValueError("weighted_terms must not be empty.")

    mean_weighted_term = float(sum(values) / len(values))
    standard_deviation = float(statistics.stdev(values)) if len(values) > 1 else 0.0
    standard_error = float(standard_deviation / math.sqrt(len(values))) if len(values) > 1 else 0.0
    return {
        "mean_weighted_term": mean_weighted_term,
        "standard_deviation": standard_deviation,
        "standard_error": standard_error,
        "min_weighted_term": float(min(values)),
        "max_weighted_term": float(max(values)),
    }


def run_tracker_basis_term_hardware(config: TrackerHardwareConfig) -> dict[str, Any]:
    """Run one tracker basis-term measurement circuit on IBM Runtime hardware."""

    context = load_tracker_instance(config.instance_id)
    active_circuit = compress_tracker_circuit_to_active_register(context)
    measurement_circuit = build_tracker_measurement_circuit(
        active_circuit,
        context.observable_active.qubits,
        config.bitstring,
    )
    service = _build_runtime_service()

    backend = _select_backend(service, config.backend, min_qubits=context.qasm_stats.active_qubits)
    transpiled = transpile(
        measurement_circuit,
        backend=backend,
        optimization_level=config.optimization_level,
        seed_transpiler=config.seed_transpiler,
        initial_layout=list(config.initial_layout) if config.initial_layout is not None else None,
    )

    if config.reuse_hardware_job_id:
        job = service.job(config.reuse_hardware_job_id)
        sampler_result = job.result()
        sampler_interface = "reused_hardware_job"
        job_id = str(config.reuse_hardware_job_id)
    else:
        job_id, sampler_result, sampler_interface, job = _run_sampler_job(
            service=service,
            backend=backend,
            circuits=[transpiled],
            shots=config.shots,
            submit_only=config.submit_only,
        )

    counts: dict[str, int] | None = None
    output_expectation: float | None = None
    input_sigma = compute_z_basis_parity(config.bitstring, context.observable_active)
    weighted_term: float | None = None
    if sampler_result is not None:
        counts = _extract_counts_list_from_sampler_result(
            sampler_result,
            shots=config.shots,
            num_bits=len(context.observable_active.qubits),
            n_items=1,
        )[0]
        output_expectation = counts_to_z_observable_expectation(
            counts,
            measured_bits=len(context.observable_active.qubits),
        )
        weighted_term = input_sigma * output_expectation

    HARDWARE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": {
            "instance_id": context.asset.instance_id,
            "tracker_label": context.asset.tracker_label,
            "delta": context.asset.delta,
            "trotter_L": context.asset.trotter_L,
            "bitstring": config.bitstring,
            "shots": config.shots,
            "backend": _backend_name(backend),
            "optimization_level": config.optimization_level,
            "seed_transpiler": config.seed_transpiler,
            "initial_layout": list(config.initial_layout) if config.initial_layout is not None else None,
            "reuse_hardware_job_id": config.reuse_hardware_job_id,
            "submit_only": config.submit_only,
        },
        "observable": {
            "source_label": context.asset.observable,
            "declared_qubits": list(context.observable_declared.qubits),
            "active_qubits": list(context.observable_active.qubits),
        },
        "perturbation_support": {
            "source": context.ole_instance.perturbation_source,
            "declared_qubits": list(context.perturbation_support_declared),
            "active_qubits": list(context.perturbation_support_active),
        },
        "transpiled": {
            "depth": int(transpiled.depth()),
            "two_qubit_gate_count": _count_two_qubit_gates(transpiled),
            "size": int(transpiled.size()),
        },
        "raw": {
            "counts": counts,
            "output_expectation": output_expectation,
            "input_sigma": input_sigma,
            "weighted_term": weighted_term,
        },
        "runtime": {
            "hardware_job_id": job_id,
            "sampler_interface": sampler_interface,
            "hardware_job_metadata": _collect_runtime_job_metadata(job, backend_name=_backend_name(backend)),
        },
        "notes": [
            "This is a single basis-term hardware probe for the published tracker circuit.",
            "It is not yet a full Monte Carlo estimate of f_delta(O).",
        ],
    }


def run_tracker_smoke_test_hardware(config: TrackerHardwareSmokeConfig) -> dict[str, Any]:
    """Run a small multi-circuit hardware smoke test as one IBM Runtime job."""

    context = load_tracker_instance(config.instance_id)
    active_circuit = compress_tracker_circuit_to_active_register(context)
    bitstrings = config.bitstrings or generate_smoke_test_bitstrings(
        n_active=context.qasm_stats.active_qubits,
        sample_count=config.sample_count,
        random_seed=config.random_seed,
    )
    for bitstring in bitstrings:
        _normalize_bitstring(bitstring, expected_length=context.qasm_stats.active_qubits)

    measurement_circuits = [
        build_tracker_measurement_circuit(active_circuit, context.observable_active.qubits, bitstring)
        for bitstring in bitstrings
    ]
    service = _build_runtime_service()
    backend = _select_backend(service, config.backend, min_qubits=context.qasm_stats.active_qubits)
    transpiled_batch = transpile(
        measurement_circuits,
        backend=backend,
        optimization_level=config.optimization_level,
        seed_transpiler=config.seed_transpiler,
        initial_layout=list(config.initial_layout) if config.initial_layout is not None else None,
    )
    transpiled_circuits = (
        [transpiled_batch] if isinstance(transpiled_batch, QuantumCircuit) else list(transpiled_batch)
    )

    job_id, sampler_result, sampler_interface, job = _run_sampler_job(
        service=service,
        backend=backend,
        circuits=transpiled_circuits,
        shots=config.shots,
        submit_only=False,
    )
    counts_list = _extract_counts_list_from_sampler_result(
        sampler_result,
        shots=config.shots,
        num_bits=len(context.observable_active.qubits),
        n_items=len(bitstrings),
    )

    records: list[dict[str, Any]] = []
    weighted_terms: list[float] = []
    for index, (bitstring, counts, transpiled_circuit) in enumerate(
        zip(bitstrings, counts_list, transpiled_circuits, strict=True)
    ):
        input_sigma = compute_z_basis_parity(bitstring, context.observable_active)
        output_expectation = counts_to_z_observable_expectation(
            counts,
            measured_bits=len(context.observable_active.qubits),
        )
        weighted_term = input_sigma * output_expectation
        weighted_terms.append(weighted_term)
        records.append(
            {
                "index": index,
                "bitstring": bitstring,
                "input_sigma": input_sigma,
                "counts": counts,
                "output_expectation": output_expectation,
                "weighted_term": weighted_term,
                "transpiled": {
                    "depth": int(transpiled_circuit.depth()),
                    "size": int(transpiled_circuit.size()),
                    "two_qubit_gate_count": _count_two_qubit_gates(transpiled_circuit),
                },
            }
        )

    HARDWARE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": {
            "instance_id": context.asset.instance_id,
            "tracker_label": context.asset.tracker_label,
            "delta": context.asset.delta,
            "trotter_L": context.asset.trotter_L,
            "sample_count": len(bitstrings),
            "shots": config.shots,
            "random_seed": config.random_seed,
            "backend": _backend_name(backend),
            "optimization_level": config.optimization_level,
            "seed_transpiler": config.seed_transpiler,
            "initial_layout": list(config.initial_layout) if config.initial_layout is not None else None,
            "bitstrings_source": "provided" if config.bitstrings is not None else "generated",
        },
        "observable": {
            "source_label": context.asset.observable,
            "declared_qubits": list(context.observable_declared.qubits),
            "active_qubits": list(context.observable_active.qubits),
        },
        "perturbation_support": {
            "source": context.ole_instance.perturbation_source,
            "declared_qubits": list(context.perturbation_support_declared),
            "active_qubits": list(context.perturbation_support_active),
        },
        "records": records,
        "aggregate": summarize_weighted_terms(weighted_terms),
        "runtime": {
            "hardware_job_id": job_id,
            "sampler_interface": sampler_interface,
            "hardware_job_metadata": _collect_runtime_job_metadata(job, backend_name=_backend_name(backend)),
        },
        "notes": [
            "This is a small hardware smoke test made of multiple tracker basis-term probes in one IBM Runtime job.",
            "It is still a partial sample and not a full Monte Carlo estimate of f_delta(O).",
        ],
    }


def parse_initial_layout(layout_text: str) -> tuple[int, ...] | None:
    """Parse a simple comma/range layout string such as `0,1,2` or `20-39`."""

    stripped = layout_text.strip()
    if not stripped:
        return None
    parts: list[int] = []
    for chunk in stripped.split(","):
        item = chunk.strip()
        if not item:
            continue
        if "-" in item:
            start_text, end_text = item.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            step = 1 if end >= start else -1
            parts.extend(range(start, end + step, step))
        else:
            parts.append(int(item))
    if not parts:
        return None
    return tuple(parts)


def list_backends(min_qubits: int) -> list[str]:
    """Return available IBM hardware backend names for the requested size."""

    service = _build_runtime_service()
    backends = service.backends(simulator=False, operational=True, min_num_qubits=min_qubits)
    return sorted(_backend_name(backend) for backend in backends)


def _build_runtime_service() -> Any:
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
    except ImportError as exc:  # pragma: no cover - depends on runtime install
        raise RuntimeError("qiskit-ibm-runtime is required for tracker hardware runs.") from exc

    token = os.getenv("QCAPI_TOKEN") or os.getenv("QISKIT_IBM_TOKEN") or os.getenv("IBM_QUANTUM_TOKEN")
    instance = os.getenv("QISKIT_IBM_INSTANCE")
    if token:
        kwargs: Dict[str, str] = {"token": token}
        if instance:
            kwargs["instance"] = instance
        try:
            return QiskitRuntimeService(channel="ibm_quantum", **kwargs)
        except TypeError:
            return QiskitRuntimeService(**kwargs)
    return QiskitRuntimeService()


def _select_backend(service: Any, requested_backend: Optional[str], min_qubits: int) -> Any:
    if requested_backend:
        return service.backend(requested_backend)

    candidates = service.backends(simulator=False, operational=True, min_num_qubits=min_qubits)
    if not candidates:
        candidates = service.backends(simulator=False, min_num_qubits=min_qubits)
    if not candidates:
        raise RuntimeError(f"No IBM hardware backend found for >= {min_qubits} qubits.")

    try:
        from qiskit_ibm_runtime import least_busy

        return least_busy(candidates)
    except Exception:
        scored: list[tuple[int, str, Any]] = []
        for backend in candidates:
            pending = 10**9
            try:
                pending = int(backend.status().pending_jobs)
            except Exception:
                pass
            scored.append((pending, _backend_name(backend), backend))
        scored.sort(key=lambda item: (item[0], item[1]))
        return scored[0][2]


def _run_sampler_job(
    *,
    service: Any,
    backend: Any,
    circuits: list[QuantumCircuit],
    shots: int,
    submit_only: bool,
) -> tuple[str, Any | None, str, Any]:
    try:
        from qiskit_ibm_runtime import SamplerV2

        sampler = SamplerV2(mode=backend)
        job = sampler.run(circuits, shots=shots)
        if submit_only:
            return str(job.job_id()), None, "SamplerV2-submit-only", job
        result = job.result()
        return str(job.job_id()), result, "SamplerV2", job
    except ImportError:  # pragma: no cover - depends on runtime install
        from qiskit_ibm_runtime import Sampler, Session

        with Session(service=service, backend=backend) as session:
            sampler = Sampler(session=session)
            job = sampler.run(circuits, shots=shots)
            if submit_only:
                return str(job.job_id()), None, "SamplerV1-submit-only", job
            result = job.result()
        return str(job.job_id()), result, "SamplerV1", job


def _extract_counts_list_from_sampler_result(
    result: Any,
    *,
    shots: int,
    num_bits: int,
    n_items: int,
) -> list[dict[str, int]]:
    if hasattr(result, "quasi_dists"):
        quasi_dists = getattr(result, "quasi_dists")
        if len(quasi_dists) < n_items:
            raise RuntimeError(f"Sampler result has {len(quasi_dists)} quasi distributions, expected >= {n_items}.")
        return [_quasi_to_counts(quasi_dist, shots=shots, num_bits=num_bits) for quasi_dist in quasi_dists[:n_items]]

    output: list[dict[str, int]] = []
    for item_index in range(n_items):
        item = None
        if isinstance(result, (list, tuple)):
            if item_index < len(result):
                item = result[item_index]
        elif hasattr(result, "__getitem__"):
            try:
                item = result[item_index]
            except Exception:
                item = None
        if item is None:
            raise RuntimeError(f"Could not index sampler result at item {item_index}.")

        counts = None
        data = getattr(item, "data", None)
        if data is not None:
            for register_name in ("c", "meas"):
                register = getattr(data, register_name, None)
                if register is not None and hasattr(register, "get_counts"):
                    counts = register.get_counts()
                    break
            if counts is None and hasattr(data, "get_counts"):
                counts = data.get_counts()
        if counts is None and hasattr(item, "get_counts"):
            counts = item.get_counts()
        if counts is None:
            raise RuntimeError(f"Could not extract counts for sampler item {item_index}.")
        output.append(_normalize_counts(counts, num_bits=num_bits))
    return output


def _normalize_counts(counts: Mapping[Any, Any], *, num_bits: int) -> dict[str, int]:
    normalized: dict[str, int] = {}
    for key, value in counts.items():
        if isinstance(key, int):
            bitstring = format(key, f"0{num_bits}b")
        else:
            bitstring = str(key).replace(" ", "").zfill(num_bits)
        normalized[bitstring] = int(round(float(value)))
    return normalized


def _quasi_to_counts(quasi_dist: Mapping[Any, Any], *, shots: int, num_bits: int) -> dict[str, int]:
    counts: dict[str, int] = {}
    for key, probability in quasi_dist.items():
        if isinstance(key, int):
            bitstring = format(key, f"0{num_bits}b")
        else:
            bitstring = str(key).replace(" ", "").zfill(num_bits)
        counts[bitstring] = int(round(float(probability) * shots))
    return counts


def _backend_name(backend: Any) -> str:
    name_attr = getattr(backend, "name", None)
    if callable(name_attr):
        try:
            return str(name_attr())
        except TypeError:
            pass
    if name_attr is not None:
        return str(name_attr)
    return str(backend)


def _count_two_qubit_gates(circuit: QuantumCircuit) -> int:
    total = 0
    for instruction in circuit.data:
        if getattr(instruction.operation, "num_qubits", 0) == 2:
            total += 1
    return total


def _collect_runtime_job_metadata(job: Any, *, backend_name: str) -> dict[str, Any]:
    metadata: dict[str, Any] = {"backend_name": backend_name}
    try:
        metadata["job_id"] = str(job.job_id())
    except Exception:
        metadata["job_id"] = None
    try:
        metadata["status"] = str(job.status())
    except Exception:
        metadata["status"] = None
    try:
        metadata["creation_date"] = _json_safe(job.creation_date())
    except Exception:
        metadata["creation_date"] = None
    try:
        metadata["usage"] = _json_safe(job.usage())
    except Exception:
        metadata["usage"] = None
    try:
        metadata["usage_estimation"] = _json_safe(job.usage_estimation)
    except Exception:
        metadata["usage_estimation"] = None
    try:
        metadata["metrics"] = _json_safe(job.metrics())
    except Exception:
        metadata["metrics"] = None
    try:
        metadata["session_id"] = _json_safe(job.session_id)
    except Exception:
        metadata["session_id"] = None
    return metadata


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "tolist"):
        try:
            return value.tolist()
        except Exception:
            pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return repr(value)


def _normalize_bitstring(bitstring: Sequence[int] | str, *, expected_length: int) -> str:
    if isinstance(bitstring, str):
        bits = tuple(int(character) for character in bitstring)
    else:
        bits = tuple(int(bit) for bit in bitstring)
    if len(bits) != expected_length:
        raise ValueError(f"Expected a bitstring of length {expected_length}, got {len(bits)}.")
    if any(bit not in (0, 1) for bit in bits):
        raise ValueError("Bitstrings may only contain 0 and 1.")
    return "".join(str(bit) for bit in bits)
