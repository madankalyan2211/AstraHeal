"""Tests for anomaly detection feature extractors, baseline models, and evaluators."""

import pytest
import numpy as np
import pandas as pd

from src.anomaly.features import AnomalyFeatureExtractor
from src.anomaly.detector import (
    StatisticalDetector,
    IsolationForestDetector,
    OneClassSVMDetector,
    CompositeAnomalyDetector,
    AnomalyReport
)
from src.anomaly.evaluation import AnomalyEvaluator


@pytest.fixture
def sample_telemetry_data():
    """Generate nominal baseline telemetry with an injected anomaly block."""
    np.random.seed(42)
    n = 200
    t = np.arange(n, dtype=float)
    v = 28.0 + np.random.normal(0, 0.05, n)
    curr = 2.0 + np.random.normal(0, 0.02, n)
    temp = 22.0 + np.random.normal(0, 0.1, n)
    
    # Inject thermal runaway anomaly from step 150 to 180
    temp[150:180] += 30.0  # Spike to 52°C
    v[150:180] -= 4.0      # Drop to 24V

    ground_truth = np.zeros(n, dtype=int)
    ground_truth[150:180] = 1

    df = pd.DataFrame({
        "timestamp": t,
        "voltage_v": v,
        "current_a": curr,
        "temperature_c": temp,
        "power_w": v * curr,
        "dt_dt": np.gradient(temp, t),
        "dv_dt": np.gradient(v, t)
    })
    return df, ground_truth


def test_anomaly_feature_extractor(sample_telemetry_data):
    df, _ = sample_telemetry_data
    extractor = AnomalyFeatureExtractor()
    extractor.fit_baseline(df.iloc[:100])
    
    z_df = extractor.compute_z_scores(df)
    assert "temperature_c_rolling_z" in z_df.columns
    
    d_m = extractor.compute_mahalanobis_distance(df)
    assert len(d_m) == len(df)
    assert np.mean(d_m[150:180]) > np.mean(d_m[:100])


def test_statistical_detector(sample_telemetry_data):
    df, y_true = sample_telemetry_data
    detector = StatisticalDetector()
    detector.fit(df.iloc[:100])
    
    reports = detector.detect_batch(df)
    assert len(reports) == len(df)
    
    # In the anomalous region, reports should trigger
    anom_reports = [reports[i] for i in range(150, 180)]
    assert any(r.is_anomaly for r in anom_reports)
    assert any("temperature_c" in r.affected_signals for r in anom_reports)

    eval_res = AnomalyEvaluator.evaluate_with_ground_truth(reports, y_true, fault_onset_index=150)
    assert eval_res["recall"] > 0.70
    assert eval_res["false_alarm_rate"] < 0.10


def test_isolation_forest_detector(sample_telemetry_data):
    df, y_true = sample_telemetry_data
    detector = IsolationForestDetector()
    detector.fit(df.iloc[:100])
    
    reports = detector.detect_batch(df)
    assert len(reports) == len(df)
    eval_res = AnomalyEvaluator.evaluate_with_ground_truth(reports, y_true, fault_onset_index=150)
    assert eval_res["precision"] > 0.50


def test_composite_ensemble_detector(sample_telemetry_data):
    df, y_true = sample_telemetry_data
    comp = CompositeAnomalyDetector([StatisticalDetector(), IsolationForestDetector()])
    comp.fit(df.iloc[:100])
    
    reports = comp.detect_batch(df)
    assert len(reports) == len(df)
    eval_res = AnomalyEvaluator.evaluate_with_ground_truth(reports, y_true)
    assert eval_res["f1_score"] > 0.60
