# Project Scope

## Goal

This project reproduces the tracker OLE benchmark as a standalone local workflow before any comparison or extension work. The first deliverable is definition-level and structural reproducibility, not early scaling claims.

## Non-Negotiable Rules

- Reproduce tracker OLE first.
- Do not mix in old proxy, locality, or scrambling metrics during reproduction.
- Keep the benchmark definition fixed before tuning simulators or extensions.
- Treat 80Q and 90Q as tracker-compatible extensions, not reproduction targets.
- Compare against the older black-hole/locality repo only after this project passes internal validation.

## Initial Deliverables

1. Tracker QASM and metadata stored locally with hashes and provenance.
2. Automated structural inspection of raw circuits.
3. Estimator definition encoded explicitly in code and docs.
4. Small definition tests for basis-state averaging and observable evaluation.
5. At least one end-to-end tracker instance pipeline that is reproducible.

## Out Of Scope For Version 0.1

- Claims about quantum advantage beyond benchmark-local evidence.
- Direct score comparisons to the older project without a mapping protocol.
- Large-scale mitigation or hardware claims before simulator-side definitions are stable.

## TODO(tracker-metadata)

- Fill in the canonical tracker asset source URLs.
- Lock the tracker naming scheme for instances such as `49x648` and `70x1872`.
- Record the tracker reference tables that define acceptable reproduction tolerances.
