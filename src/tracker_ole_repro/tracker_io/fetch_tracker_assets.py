"""Fetch canonical Quantum Advantage Tracker OLE assets with provenance."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.request import urlopen
import argparse

from tracker_ole_repro.circuits.inspect_qasm import QasmInspectionResult, inspect_qasm_path, write_qasm_stats_csv
from tracker_ole_repro.paths import QASM_STATS_CSV, TRACKER_METADATA_DIR, TRACKER_QASM_DIR

TRACKER_PAGE_URL = "https://quantum-advantage-tracker.github.io/trackers/observable-estimations"
TRACKER_REPOSITORY_URL = "https://github.com/quantum-advantage-tracker/quantum-advantage-tracker.github.io"
TRACKER_README_URL = (
    "https://raw.githubusercontent.com/quantum-advantage-tracker/quantum-advantage-tracker.github.io/"
    "main/data/observable-estimations/circuit-models/operator_loschmidt_echo/README.md"
)


@dataclass(frozen=True, slots=True)
class TrackerAssetDefinition:
    """Canonical public tracker asset with minimal benchmark metadata."""

    instance_id: str
    tracker_label: str
    file_name: str
    source_url: str
    num_qubits: int
    trotter_L: int
    delta: float
    observable: str


TRACKER_ASSETS: tuple[TrackerAssetDefinition, ...] = (
    TrackerAssetDefinition(
        instance_id="operator_loschmidt_echo_49x648",
        tracker_label="49x648",
        file_name="49Q_OLE_circuit_L_3_b_0.25_delta0.15.qasm",
        source_url=(
            "https://raw.githubusercontent.com/quantum-advantage-tracker/quantum-advantage-tracker.github.io/"
            "main/data/observable-estimations/circuit-models/operator_loschmidt_echo/"
            "49Q_OLE_circuit_L_3_b_0.25_delta0.15.qasm"
        ),
        num_qubits=49,
        trotter_L=3,
        delta=0.15,
        observable="Z52 Z59 Z72",
    ),
    TrackerAssetDefinition(
        instance_id="operator_loschmidt_echo_49x1296",
        tracker_label="49x1296",
        file_name="49Q_OLE_circuit_L_6_b_0.25_delta0.15.qasm",
        source_url=(
            "https://raw.githubusercontent.com/quantum-advantage-tracker/quantum-advantage-tracker.github.io/"
            "main/data/observable-estimations/circuit-models/operator_loschmidt_echo/"
            "49Q_OLE_circuit_L_6_b_0.25_delta0.15.qasm"
        ),
        num_qubits=49,
        trotter_L=6,
        delta=0.15,
        observable="Z52 Z59 Z72",
    ),
    TrackerAssetDefinition(
        instance_id="operator_loschmidt_echo_70x1872",
        tracker_label="70x1872",
        file_name="70Q_OLE_circuit_L_6_b_0.25_delta0.15.qasm",
        source_url=(
            "https://raw.githubusercontent.com/quantum-advantage-tracker/quantum-advantage-tracker.github.io/"
            "main/data/observable-estimations/circuit-models/operator_loschmidt_echo/"
            "70Q_OLE_circuit_L_6_b_0.25_delta0.15.qasm"
        ),
        num_qubits=70,
        trotter_L=6,
        delta=0.15,
        observable="Z52 Z59 Z72",
    ),
)


def fetch_tracker_assets(*, overwrite: bool = False) -> list[dict[str, Any]]:
    """Fetch all canonical tracker OLE QASM assets and metadata sidecars."""

    TRACKER_QASM_DIR.mkdir(parents=True, exist_ok=True)
    TRACKER_METADATA_DIR.mkdir(parents=True, exist_ok=True)

    readme_snapshot_path = TRACKER_METADATA_DIR / "operator_loschmidt_echo_README.md"
    readme_text = _download_text(TRACKER_README_URL)
    if overwrite or not readme_snapshot_path.exists():
        readme_snapshot_path.write_text(readme_text, encoding="utf-8")

    fetched_records: list[dict[str, Any]] = []
    for asset in TRACKER_ASSETS:
        qasm_bytes = _download_bytes(asset.source_url)
        qasm_path = TRACKER_QASM_DIR / asset.file_name
        if overwrite or not qasm_path.exists():
            qasm_path.write_bytes(qasm_bytes)

        sha256 = hashlib.sha256(qasm_bytes).hexdigest()
        metadata = {
            **asdict(asset),
            "tracker_page_url": TRACKER_PAGE_URL,
            "source_repository_url": TRACKER_REPOSITORY_URL,
            "source_readme_url": TRACKER_README_URL,
            "source_readme_snapshot": _relative_project_path(readme_snapshot_path),
            "local_path": _relative_project_path(qasm_path),
            "sha256": sha256,
            "notes": "Canonical tracker raw qasm fetched without modification.",
        }
        metadata_path = TRACKER_METADATA_DIR / f"{asset.instance_id}.json"
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
        fetched_records.append(metadata)

    index_path = TRACKER_METADATA_DIR / "tracker_asset_index.json"
    index_payload = {
        "family": "operator_loschmidt_echo",
        "tracker_page_url": TRACKER_PAGE_URL,
        "source_repository_url": TRACKER_REPOSITORY_URL,
        "assets": fetched_records,
    }
    index_path.write_text(json.dumps(index_payload, indent=2, sort_keys=True), encoding="utf-8")
    return fetched_records


def inspect_fetched_tracker_assets(*, output_path: str | Path = QASM_STATS_CSV) -> Path:
    """Inspect all fetched tracker QASM files and write a consolidated CSV."""

    results: list[QasmInspectionResult] = []
    for asset in TRACKER_ASSETS:
        qasm_path = TRACKER_QASM_DIR / asset.file_name
        if not qasm_path.exists():
            raise FileNotFoundError(f"Missing fetched QASM asset: {qasm_path}")
        results.append(inspect_qasm_path(qasm_path, instance_id=asset.instance_id))
    return write_qasm_stats_csv(results, output_path)


def main() -> None:
    """CLI entry point for fetching and optionally inspecting tracker assets."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--overwrite", action="store_true", help="Refetch and overwrite existing files.")
    parser.add_argument("--inspect", action="store_true", help="Generate data/processed/qasm_stats.csv after fetch.")
    args = parser.parse_args()

    records = fetch_tracker_assets(overwrite=args.overwrite)
    print(f"Fetched {len(records)} tracker assets into {TRACKER_QASM_DIR}")
    if args.inspect:
        output_path = inspect_fetched_tracker_assets()
        print(f"Wrote structural QASM stats to {output_path}")


def _download_bytes(url: str) -> bytes:
    with urlopen(url) as response:
        return response.read()


def _download_text(url: str) -> str:
    return _download_bytes(url).decode("utf-8")


def _relative_project_path(path: Path) -> str:
    return path.relative_to(Path(__file__).resolve().parents[3]).as_posix()


if __name__ == "__main__":
    main()
