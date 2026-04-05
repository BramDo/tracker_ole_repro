"""Inspect canonical tracker QASM files and print a compact summary."""

from __future__ import annotations

import argparse

from tracker_ole_repro.tracker_io.fetch_tracker_assets import fetch_tracker_assets, inspect_fetched_tracker_assets
from tracker_ole_repro.tracker_io.load_tracker_instance import list_tracker_asset_definitions, load_tracker_instance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance-id", help="Inspect a single canonical tracker instance.")
    args = parser.parse_args()

    fetch_tracker_assets(overwrite=False)
    inspect_fetched_tracker_assets()

    if args.instance_id:
        contexts = [load_tracker_instance(args.instance_id)]
    else:
        contexts = [load_tracker_instance(asset.instance_id) for asset in list_tracker_asset_definitions()]

    for context in contexts:
        print(
            f"{context.asset.instance_id}: declared={context.qasm_stats.declared_qubits}, "
            f"active={context.qasm_stats.active_qubits}, total_gates={context.qasm_stats.total_gate_count}, "
            f"cz={context.qasm_stats.cz_count}, depth={context.qasm_stats.depth}, "
            f"observable_declared={context.observable_declared.qubits}, "
            f"observable_active={context.observable_active.qubits}, "
            f"perturbation_support_declared={context.perturbation_support_declared}, "
            f"perturbation_support_active={context.perturbation_support_active}"
        )


if __name__ == "__main__":
    main()
