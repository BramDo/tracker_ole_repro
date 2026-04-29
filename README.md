# tracker_ole_repro

Reproduction-first scaffold for a local Windows workflow that rebuilds the tracker OLE benchmark before any 80/90-qubit extension work.

## Project Rules

- Reproduce tracker OLE before adding new circuit families.
- Keep circuit parsing, estimator logic, simulation, and analysis separate.
- Treat 80Q and 90Q work as extensions, not as benchmark reproduction claims.
- Compare against the earlier black-hole/locality project only after internal validation.

## Workflow

1. Fetch tracker assets
2. Inspect raw QASM
3. Validate estimator semantics
4. Reproduce 49Q and 70Q reference instances
5. Extend to 80Q and 90Q with tracker-compatible semantics
6. Compare to older black-hole/locality project

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest
$env:PYTHONPATH='src'
python -m tracker_ole_repro.tracker_io.fetch_tracker_assets --inspect
```

## IBM Hardware Path

This project now mirrors the existing qlab launch pattern: Windows PowerShell wrapper -> WSL -> qiskit virtual environment -> IBM Runtime runner.

Dry-run the Windows wrapper first:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_tracker_49q_hardware.ps1 -DryRun
```

Submit a real IBM job without waiting for completion:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_tracker_49q_hardware.ps1 `
  -RunLabel submit_20260402a `
  -Backend ibm_fez `
  -Shots 256 `
  -SubmitOnly
```

Run the hardware CLI directly from Python when the IBM Runtime package and credentials are available:

```powershell
$env:PYTHONPATH='src'
python -m tracker_ole_repro.cli.run_tracker_hardware `
  --instance-id operator_loschmidt_echo_49x648 `
  --backend ibm_fez `
  --shots 4000 `
  --output-json data/results/hardware/operator_loschmidt_echo_49x648_manual.json
```

Expected credentials follow the qlab convention:

- `QCAPI_TOKEN`
- `IBM_QUANTUM_TOKEN`
- optional `QISKIT_IBM_INSTANCE`

## Layout

- `docs/` captures scope and reproduction criteria.
- `data/raw/` is for tracker QASM and metadata.
- `data/processed/` holds structural circuit summaries.
- `data/results/` holds estimator and simulation outputs.
- `src/tracker_ole_repro/` contains the Python package.
- `tests/` keeps small semantic and parser checks green before large runs.

## Current Scope

This first version sets up the baseline documentation, a QASM structure inspector, a small OLE estimator core, a tracker asset fetcher, and a Qiskit Aer runner interface. Tracker-specific metadata wiring is intentionally left behind explicit `TODO(tracker-metadata)` markers only where the public source material still leaves choices open.
