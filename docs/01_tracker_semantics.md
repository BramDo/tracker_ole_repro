# Tracker Semantics

## Purpose

This file fixes the benchmark semantics that the code must preserve. It exists to prevent the common failure mode where a QASM circuit is reproduced structurally but the estimator being evaluated has drifted.

## Benchmark Object

The target quantity is the tracker OLE observable expectation

`f_delta(O) = (1 / 2^n) Tr(U O U^dagger V_delta^dagger U O U^dagger V_delta)`.

The tracker source README defines the perturbation as `V_delta = exp(-i delta G)` and states that `O` must satisfy `Tr(O^2) = 1`.

At minimum, the benchmark definition must keep the following pieces separate:

- `U`: the base unitary circuit encoded by the tracker QASM.
- `V_delta`: the perturbation or delta-dependent part of the evolution.
- `O`: the fixed observable or observable family that is evaluated after evolution.
- Computational-basis initial states: the benchmark averages over sampled or enumerated basis states and is not reducible to a single-run bitstring overlap.

For the released tracker OLE circuit family used here, the upstream source README specifies:

- `G = sum_{u in P} X_u`
- `U = (U_-b^dagger)^L U_b^L`
- `U_b = prod_{E in cal(E)} prod_{(u,v) in E} exp(-i pi/4 Z_u Z_v) exp(-i pi/8 (Z_u + Z_v)) exp(-i (b_u X_u + b_v X_v))`
- the canonical observables for `49x648`, `49x1296`, and `70x1872` are all `O = Z52 Z59 Z72`
- `delta = 0.15` for all three canonical instances

## Practical Semantics

- The QASM file describes the circuit unitary only.
- The QASM file does not, by itself, define the full estimator.
- State preparation is a separate semantic step.
- Observable evaluation is a separate semantic step.
- Averaging over computational-basis initial states is part of the estimator, not an implementation detail.

The upstream README also fixes the sampled estimator form:

`f_delta(O) = (1 / 2^n) sum_z sigma_z <z | U^dagger V_delta^dagger U O U^dagger V_delta | z>`

with `sigma_z = <z|O|z> in {+1, -1}` and a Monte Carlo approximation over uniformly drawn computational-basis states `z_i`.

## Result Categories

The code and result tables should distinguish at least these categories:

- `raw`: direct simulated or measured estimator output.
- `rescaled`: benchmark output after any tracker-defined normalization.
- `mitigated`: output after an explicitly documented mitigation procedure.

These labels should never be collapsed into a single unnamed score.

## Anti-Drift Rules

- Do not replace basis-state averaging with one-shot overlap proxies.
- Do not infer observable placement from QASM alone unless the tracker metadata says so.
- Do not merge simulator settings into the semantic definition of the estimator.
- Do not compare new extension instances to tracker reproduction claims without labelling them as extensions.

## TODO(tracker-metadata)

- Record the exact perturbation-site set `P` for each reference instance.
- Record the exact `F` and `S` lattice partition used to define the site-dependent `b_u`.
- Record the tracker distinction between raw, rescaled, and mitigated outputs together with the exact rescaling convention used on the public tracker page.
