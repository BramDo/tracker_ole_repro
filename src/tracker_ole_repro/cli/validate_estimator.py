"""Validate tracker observable mapping and basis-state parity semantics."""

from __future__ import annotations

import argparse

from tracker_ole_repro.estimator.validation import compute_z_basis_parity
from tracker_ole_repro.tracker_io.fetch_tracker_assets import fetch_tracker_assets
from tracker_ole_repro.tracker_io.load_tracker_instance import load_tracker_instance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--instance-id",
        default="operator_loschmidt_echo_49x648",
        help="Canonical tracker instance to validate.",
    )
    args = parser.parse_args()

    fetch_tracker_assets(overwrite=False)
    context = load_tracker_instance(args.instance_id)

    zero_state = tuple(0 for _ in range(context.ole_instance.n_active))
    single_flip = list(zero_state)
    single_flip[context.observable_active.qubits[0]] = 1
    double_flip = single_flip.copy()
    if len(context.observable_active.qubits) > 1:
        double_flip[context.observable_active.qubits[1]] = 1

    print(f"instance_id={context.asset.instance_id}")
    print(f"observable_declared={context.observable_declared.qubits}")
    print(f"observable_active={context.observable_active.qubits}")
    print(f"zero_state_sigma={compute_z_basis_parity(zero_state, context.observable_active)}")
    print(f"single_flip_sigma={compute_z_basis_parity(single_flip, context.observable_active)}")
    print(f"double_flip_sigma={compute_z_basis_parity(double_flip, context.observable_active)}")


if __name__ == "__main__":
    main()
