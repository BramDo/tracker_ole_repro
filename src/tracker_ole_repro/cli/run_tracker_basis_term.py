"""Run one basis-state contribution through a published tracker OLE circuit."""

from __future__ import annotations

import argparse

from tracker_ole_repro.simulation.tracker_runner import run_tracker_basis_term


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance-id", default="operator_loschmidt_echo_49x648")
    parser.add_argument(
        "--bitstring",
        default=None,
        help="Active-register bitstring; defaults to the all-zero state for the selected instance.",
    )
    parser.add_argument("--simulator-method", default="matrix_product_state")
    parser.add_argument("--length", type=int, default=None, help="Optional explicit length for zero-state generation.")
    args = parser.parse_args()

    if args.bitstring is None:
        zero_length = args.length or 49
        bitstring = "0" * zero_length
    else:
        bitstring = args.bitstring

    result = run_tracker_basis_term(
        args.instance_id,
        bitstring,
        simulator_method=args.simulator_method,
    )
    print(f"instance_id={result.instance_id}")
    print(f"simulator_method={result.simulator_method}")
    print(f"input_sigma={result.input_sigma}")
    print(f"output_expectation={result.output_expectation}")
    print(f"weighted_term={result.weighted_term}")
    print(f"observable_active={result.observable_active}")
    print(f"perturbation_support_active={result.perturbation_support_active}")


if __name__ == "__main__":
    main()
