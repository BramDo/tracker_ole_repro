# Tracker Definition

## Purpose

This file fixes the benchmark definition that the code must preserve. It exists to prevent the common failure mode where a QASM circuit is reproduced structurally but the estimator being evaluated has drifted.

## Benchmark Object

The target quantity is the tracker OLE observable expectation

`f_delta(O) = (1 / 2^n) Tr(U O U^dagger V_delta^dagger U O U^dagger V_delta)`.

The tracker source README defines the perturbation as `V_delta = exp(-i delta G)` and states that `O` must satisfy `Tr(O^2) = 1`.

At minimum, the benchmark definition must keep the following pieces separate:

- `U`: the base unitary circuit encoded by the tracker QASM.
- `V_delta`: the perturbation or delta-dependent part of the evolution.
- `O`: the fixed observable or observable family that is evaluated after evolution.
- Computational-basis initial states: the benchmark averages over sampled or enumerated basis states and is not reducible to a single-run bitstring overlap.

## Practical Rules

- The QASM file describes the circuit unitary only.
- The QASM file does not define the full estimator.
- State preparation is a separate step.
- Observable evaluation is a separate step.
- Averaging over computational-basis initial states is part of the estimator.

## Anti-Drift Rules

- Do not replace basis-state averaging with one-shot overlap proxies.
- Do not infer observable placement from QASM alone unless metadata confirms it.
- Do not merge simulator settings into the benchmark definition.
- Do not present extensions as reproductions.
