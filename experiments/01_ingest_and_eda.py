"""Experiment 01: Ingestion of NASA PCoE Battery Aging Dataset, Preprocessing, and EDA.

Demonstrates:
- Ingestion of raw dataset into immutable storage
- Provenance recording (URL, citation, SHA256 checksum)
- Preprocessing and feature engineering
- Generation of publication-quality diagnostic plots
"""

import sys
from pathlib import Path

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import json
from src.telemetry.data_loader import NASABatteryDataLoader
from src.telemetry.preprocess import TelemetryPreprocessor
from src.telemetry.visualization import TelemetryVisualizer
from src.telemetry.provenance import DatasetProvenanceTracker


def run_experiment():
    print("=" * 70)
    print("ASTRAHEAL EXPERIMENT 01: NASA PCoE Battery Ingestion & EDA")
    print("=" * 70)

    # 1. Ingest raw benchmark dataset
    loader = NASABatteryDataLoader(raw_dir="data/raw", processed_dir="data/processed")
    raw_path = loader.generate_reproducible_benchmark_dataset(battery_id="B0005", num_cycles=168)
    print(f"[+] Raw dataset stored at: {raw_path}")

    # 2. Check provenance
    tracker = DatasetProvenanceTracker()
    meta = tracker.get_provenance("NASA_PCOE_BENCHMARK_B0005")
    if meta:
        print(f"[+] Provenance verified: {meta.dataset_name}")
        print(f"    Source: {meta.source_url}")
        print(f"    Citation: {meta.citation}")
        print(f"    Checksum: {list(meta.file_hashes_sha256.values())[0]}")

    # 3. Preprocess and extract features
    preprocessor = TelemetryPreprocessor(processed_dir="data/processed")
    feat_df, summary = preprocessor.process_and_save(raw_path, "nasa_pcoe_b0005_processed.csv")
    print(f"[+] Preprocessed {len(feat_df)} telemetry samples across {len(feat_df.columns)} channels.")
    print(f"    Cleaning stats: {summary['cleaning_stats']}")

    # 4. Generate Visualizations
    vis = TelemetryVisualizer(output_dir="docs/figures")
    
    # Time series sample (first 1000s)
    sample_df = feat_df.iloc[:1000]
    p1 = vis.plot_telemetry_trends(sample_df, "01_nasa_battery_telemetry_trends.png", "NASA PCoE Battery (B0005) Telemetry Trends")
    print(f"[+] Saved trend plot: {p1}")

    # Correlations
    p2 = vis.plot_correlation_matrix(feat_df, "01_nasa_battery_correlations.png")
    print(f"[+] Saved correlation plot: {p2}")

    # Degradation trajectory
    p3 = vis.plot_degradation_trajectory(feat_df, "01_nasa_battery_degradation.png")
    print(f"[+] Saved degradation trajectory plot: {p3}")

    print("\n[✓] Stage 2 & 3 Data Ingestion & Preprocessing Experiment Complete.")


if __name__ == "__main__":
    run_experiment()
