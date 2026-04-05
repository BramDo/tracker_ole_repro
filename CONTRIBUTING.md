# Contributing

## Scope First

- Keep this repository reproduction-first.
- Treat tracker benchmark reproduction and later 80Q/90Q extensions as separate phases.
- Do not mix black-hole or locality-specific diagnostics into the core tracker reproduction path.

## Before You Change Code

- Read `README.md` and the files in `docs/`.
- Preserve the distinction between circuit loading, estimator logic, simulation, and analysis.
- Keep tracker-specific assumptions explicit in code and docs, especially for `V_delta`, perturbation support, and observable placement.

## Development Rules

- Use `pathlib` for filesystem paths.
- Keep type hints on new public functions.
- Prefer compact, auditable outputs over ad hoc notebooks or hidden state.
- Do not silently change benchmark semantics to match easier simulations.

## Validation

Run the local test suite before pushing changes:

```bash
python -m pytest -p no:cacheprovider
```

If you touch the hardware path, also verify the CLI entrypoints and keep the run metadata reproducible.

## Data and Results

- Canonical raw tracker assets in `data/raw/` belong to the repo.
- Derived CSV and result JSON outputs are generally ignored unless they are intentional reference artifacts.
- Keep source URLs, hashes, seeds, backend names, and job ids explicit in saved metadata.

## Pull Requests

- Keep PRs narrow.
- Explain whether the change affects reproduction, extension, or comparison work.
- Call out any remaining unknown tracker metadata instead of hiding it behind defaults.
