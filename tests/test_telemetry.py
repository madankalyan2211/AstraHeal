"""Tests for telemetry schemas, validation, data loaders, and preprocessing."""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

from src.telemetry.schema import TelemetryFrame, TelemetryBatch, OperatingState
from src.telemetry.provenance import DatasetMetadata, DatasetProvenanceTracker
from src.telemetry.data_loader import NASABatteryDataLoader, SimulatedTelemetryLoader
from src.telemetry.preprocess import TelemetryPreprocessor


def test_telemetry_frame_validation():
    """Test valid creation and physical boundary validation for TelemetryFrame."""
    frame = TelemetryFrame(
        timestamp=100.0,
        system_id="TEST-SC-01",
        subsystem="EPS",
        voltage_v=28.4,
        current_a=2.5,
        temperature_c=22.1,
        capacity_ah=38.5,
        state_of_charge=0.92,
        operating_state=OperatingState.NOMINAL
    )
    assert frame.voltage_v == 28.4
    assert frame.operating_state == OperatingState.NOMINAL

    # Out of physical bound should raise ValueError
    with pytest.raises(ValueError):
        TelemetryFrame(timestamp=0, voltage_v=600.0, current_a=0, temperature_c=20)

    with pytest.raises(ValueError):
        TelemetryFrame(timestamp=0, voltage_v=28.0, current_a=0, temperature_c=500.0)


def test_telemetry_batch_dataframe_conversion():
    """Test batch conversion to and from pandas DataFrame."""
    frames = [
        TelemetryFrame(timestamp=float(t), voltage_v=28.0 - t*0.01, current_a=1.5, temperature_c=20.0 + t*0.1)
        for t in range(5)
    ]
    batch = TelemetryBatch(frames)
    df = batch.to_dataframe()
    assert len(df) == 5
    assert "voltage_v" in df.columns
    assert "current_a" in df.columns

    restored = TelemetryBatch.from_dataframe(df)
    assert len(restored) == 5
    assert restored[0].timestamp == 0.0
    assert abs(restored[4].voltage_v - 27.96) < 1e-4


def test_provenance_tracker(tmp_path):
    """Test recording and verifying provenance hashes."""
    tracker = DatasetProvenanceTracker(metadata_dir=str(tmp_path))
    test_file = tmp_path / "sample.csv"
    test_file.write_text("timestamp,voltage_v\n0.0,28.0\n")

    file_hash = tracker.compute_sha256(test_file)
    meta = DatasetMetadata(
        dataset_name="TEST_DATASET",
        source_url="https://example.org/test",
        license_or_terms="MIT",
        citation="Test Citation 2026",
        description="Unit test dataset",
        file_hashes_sha256={"sample.csv": file_hash}
    )
    tracker.record_provenance(meta)

    # Verification
    res = tracker.verify_integrity("TEST_DATASET", tmp_path)
    assert res["sample.csv"] is True


def test_nasa_benchmark_generation(tmp_path):
    """Test deterministic NASA benchmark generation."""
    loader = NASABatteryDataLoader(raw_dir=str(tmp_path / "raw"), processed_dir=str(tmp_path / "processed"))
    out_file = loader.generate_reproducible_benchmark_dataset(battery_id="BTEST", num_cycles=3)
    assert out_file.exists()
    df = pd.read_csv(out_file)
    assert len(df) > 50
    assert "capacity_ah" in df.columns
    assert "hi_soh" in df.columns


def test_preprocessor_pipeline(tmp_path):
    """Test cleaning and feature engineering in preprocessor."""
    prep = TelemetryPreprocessor(processed_dir=str(tmp_path / "processed"))
    raw_df = pd.DataFrame({
        "timestamp": [1.0, 2.0, 2.0, 3.0, 4.0],  # Duplicate timestamp at 2.0
        "voltage_v": [28.0, 27.9, 27.9, np.nan, 27.7],  # Missing value
        "current_a": [2.0, 2.0, 2.0, 2.0, 2.0],
        "temperature_c": [20.0, 20.1, 20.1, 20.2, 20.3]
    })
    
    cleaned_df, stats = prep.validate_and_clean(raw_df)
    assert len(cleaned_df) == 4
    assert stats["duplicate_timestamps_dropped"] == 1
    assert stats["missing_values_imputed"] == 1
    assert not cleaned_df["voltage_v"].isna().any()

    feat_df = prep.extract_features(cleaned_df)
    assert "power_w" in feat_df.columns
    assert "dv_dt" in feat_df.columns
    assert "dt_dt" in feat_df.columns
    assert "voltage_v_rolling_mean" in feat_df.columns
