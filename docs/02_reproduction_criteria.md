# Reproduction Criteria

## Reproduction Levels

1. File reproduction
   The locally fetched tracker files match the canonical upstream filenames, hashes are recorded, and provenance is stored.
2. Circuit reproduction
   Structural facts match the tracker source: declared qubits, active qubits, total gate count, depth class, and observable placement metadata where available.
3. Estimator reproduction
   The local code reproduces the tracker estimator semantics: computational-basis averaging, parity weighting, observable evaluation, and explicit random-seed logging when sampling is used.
4. Result reproduction
   Local results agree with published tracker values within an explicit tolerance and with the same label semantics, for example `raw`, `rescaled`, or `mitigated`.

## Naming Rule

Only call a run "reproduced" once all four levels above have been checked for that instance. Structural agreement alone is not enough.

## Canonical First Targets

- `operator_loschmidt_echo_49x648`
- `operator_loschmidt_echo_49x1296`
- `operator_loschmidt_echo_70x1872`

## Minimum Evidence To Keep

- fetched QASM files
- metadata sidecars with source URL and SHA256
- generated `qasm_stats.csv`
- estimator configuration logs
- a short validation note that records which reproduction level has been passed
