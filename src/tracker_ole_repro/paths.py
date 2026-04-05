"""Project-relative paths for Windows-friendly local workflows."""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PACKAGE_ROOT.parent
PROJECT_ROOT = SRC_ROOT.parent
DOCS_DIR = PROJECT_ROOT / "docs"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
TRACKER_QASM_DIR = RAW_DATA_DIR / "tracker_qasm"
TRACKER_METADATA_DIR = RAW_DATA_DIR / "tracker_metadata"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
HARDWARE_RESULTS_DIR = RESULTS_DIR / "hardware"
QASM_STATS_CSV = PROCESSED_DATA_DIR / "qasm_stats.csv"
