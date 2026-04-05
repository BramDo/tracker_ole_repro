"""Run a small batched tracker hardware smoke test on IBM Runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tracker_ole_repro.paths import HARDWARE_RESULTS_DIR
from tracker_ole_repro.simulation.tracker_hardware_runner import (
    TrackerHardwareSmokeConfig,
    parse_initial_layout,
    run_tracker_smoke_test_hardware,
)
from tracker_ole_repro.tracker_io.fetch_tracker_assets import fetch_tracker_assets


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance-id", default="operator_loschmidt_echo_49x648")
    parser.add_argument("--sample-count", type=int, default=4)
    parser.add_argument("--shots", type=int, default=256)
    parser.add_argument("--random-seed", type=int, default=424242)
    parser.add_argument("--backend", default="ibm_fez")
    parser.add_argument("--optimization-level", type=int, default=1)
    parser.add_argument("--seed-transpiler", type=int, default=424242)
    parser.add_argument("--initial-layout", default="")
    parser.add_argument(
        "--output-json",
        default=None,
        help="Output path relative to the project root; defaults to data/results/hardware/<instance>_smoke.json",
    )
    args = parser.parse_args()

    fetch_tracker_assets(overwrite=False)
    payload = run_tracker_smoke_test_hardware(
        TrackerHardwareSmokeConfig(
            instance_id=args.instance_id,
            sample_count=args.sample_count,
            shots=args.shots,
            random_seed=args.random_seed,
            backend=args.backend or None,
            optimization_level=args.optimization_level,
            seed_transpiler=args.seed_transpiler,
            initial_layout=parse_initial_layout(args.initial_layout),
        )
    )

    output_path = (
        Path(args.output_json)
        if args.output_json
        else HARDWARE_RESULTS_DIR / f"{args.instance_id}_smoke_{args.sample_count}s_{args.shots}shots.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    print(f"instance_id={payload['config']['instance_id']}")
    print(f"backend={payload['config']['backend']}")
    print(f"hardware_job_id={payload['runtime']['hardware_job_id']}")
    print(f"sample_count={payload['config']['sample_count']}")
    print(f"mean_weighted_term={payload['aggregate']['mean_weighted_term']}")
    print(f"standard_error={payload['aggregate']['standard_error']}")
    print(f"output_json={output_path}")


if __name__ == "__main__":
    main()
