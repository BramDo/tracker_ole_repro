"""Run one tracker basis-term probe on IBM Runtime hardware."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from tracker_ole_repro.paths import HARDWARE_RESULTS_DIR
from tracker_ole_repro.simulation.tracker_hardware_runner import (
    TrackerHardwareConfig,
    list_backends,
    parse_initial_layout,
    run_tracker_basis_term_hardware,
)
from tracker_ole_repro.tracker_io.fetch_tracker_assets import fetch_tracker_assets
from tracker_ole_repro.tracker_io.load_tracker_instance import load_tracker_instance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance-id", default="operator_loschmidt_echo_49x648")
    parser.add_argument("--bitstring", default=None)
    parser.add_argument("--shots", type=int, default=4000)
    parser.add_argument("--backend", default="ibm_fez")
    parser.add_argument("--optimization-level", type=int, default=1)
    parser.add_argument("--seed-transpiler", type=int, default=424242)
    parser.add_argument("--initial-layout", default="")
    parser.add_argument("--reuse-hardware-job-id", default=None)
    parser.add_argument("--submit-only", action="store_true")
    parser.add_argument("--list-backends", action="store_true")
    parser.add_argument(
        "--output-json",
        default=None,
        help="Output path relative to the project root; defaults to data/results/hardware/<instance>.json",
    )
    args = parser.parse_args()

    fetch_tracker_assets(overwrite=False)
    context = load_tracker_instance(args.instance_id)

    if args.list_backends:
        for backend_name in list_backends(min_qubits=context.qasm_stats.active_qubits):
            print(backend_name)
        return

    bitstring = args.bitstring or ("0" * context.qasm_stats.active_qubits)
    config = TrackerHardwareConfig(
        instance_id=args.instance_id,
        bitstring=bitstring,
        shots=args.shots,
        backend=args.backend or None,
        optimization_level=args.optimization_level,
        seed_transpiler=args.seed_transpiler,
        initial_layout=parse_initial_layout(args.initial_layout),
        reuse_hardware_job_id=args.reuse_hardware_job_id,
        submit_only=args.submit_only,
    )
    payload = run_tracker_basis_term_hardware(config)

    output_path = Path(args.output_json) if args.output_json else HARDWARE_RESULTS_DIR / f"{args.instance_id}_basis_term.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    print(f"instance_id={payload['config']['instance_id']}")
    print(f"backend={payload['config']['backend']}")
    print(f"hardware_job_id={payload['runtime']['hardware_job_id']}")
    print(f"output_expectation={payload['raw']['output_expectation']}")
    print(f"weighted_term={payload['raw']['weighted_term']}")
    print(f"output_json={output_path}")


if __name__ == "__main__":
    main()
