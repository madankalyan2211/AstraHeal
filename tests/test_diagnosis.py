"""Tests for fault diagnosis engines, hypothesis distributions, and uncertainty calibration."""

import pytest
import numpy as np
import pandas as pd

from src.anomaly.detector import AnomalyReport
from src.diagnosis.schema import DiagnosisReport, DiagnosisStatus, FailureMode
from src.diagnosis.rules import PhysicsRuleDiagnosticEngine
from src.diagnosis.bayesian import BayesianEvidentialDiagnosticEngine
from src.diagnosis.engine import FaultDiagnosisEngine


def test_insufficient_evidence_when_nominal():
    """Ensure system returns INSUFFICIENT_EVIDENCE when anomaly score is low."""
    rep = AnomalyReport(
        timestamp=10.0,
        anomaly_score=0.05,
        is_anomaly=False,
        affected_signals=[],
        detector_name="StatisticalDetector"
    )
    row = pd.Series({"voltage_v": 28.0, "current_a": 2.0, "temperature_c": 21.0})
    
    engine = FaultDiagnosisEngine()
    diag = engine.diagnose_frame(rep, row)
    assert diag.status == DiagnosisStatus.INSUFFICIENT_EVIDENCE
    assert diag.primary_failure_mode == FailureMode.NOMINAL_OPERATION.value


def test_known_failure_thermal_runaway():
    """Ensure thermal runaway signature is diagnosed as KNOWN_FAILURE with high confidence."""
    rep = AnomalyReport(
        timestamp=150.0,
        anomaly_score=0.95,
        is_anomaly=True,
        affected_signals=["temperature_c"],
        detector_name="StatisticalDetector"
    )
    # Severe thermal signature: 52°C, high dT/dt
    row = pd.Series({
        "voltage_v": 25.0,
        "current_a": 6.0,
        "temperature_c": 52.0,
        "power_w": 150.0,
        "dv_dt": -0.04,
        "dt_dt": 0.12,
        "est_r_int": 0.08
    })

    engine = FaultDiagnosisEngine(primary_method="bayesian")
    diag = engine.diagnose_frame(rep, row)
    assert diag.status == DiagnosisStatus.KNOWN_FAILURE
    assert diag.primary_failure_mode == FailureMode.THERMAL_RUNAWAY_INITIATION.value
    assert diag.confidence > 0.60
    assert diag.epistemic_uncertainty < 0.40


def test_unknown_failure_when_unseen_ood():
    """Ensure system declares UNKNOWN_FAILURE with high epistemic uncertainty on unseen anomalies."""
    rep = AnomalyReport(
        timestamp=300.0,
        anomaly_score=0.92,
        is_anomaly=True,
        affected_signals=["voltage_v", "temperature_c"],
        detector_name="StatisticalDetector"
    )
    # Completely unphysical / out-of-distribution point not matching any known failure cluster
    row = pd.Series({
        "voltage_v": 3.0,
        "current_a": -45.0,
        "temperature_c": -90.0,
        "power_w": -135.0,
        "dv_dt": -12.0,
        "dt_dt": -8.0,
        "est_r_int": 15.0
    })

    engine = FaultDiagnosisEngine(primary_method="bayesian")
    diag = engine.diagnose_frame(rep, row)
    assert diag.status == DiagnosisStatus.UNKNOWN_FAILURE
    assert diag.primary_failure_mode == FailureMode.NOVEL_UNSEEN_ANOMALY.value
    assert diag.epistemic_uncertainty > 0.60


def test_rule_and_bayesian_comparison():
    """Test comparative diagnosis output across rule and bayesian engines."""
    rep = AnomalyReport(
        timestamp=50.0,
        anomaly_score=0.88,
        is_anomaly=True,
        affected_signals=["voltage_v"],
        detector_name="StatisticalDetector"
    )
    row = pd.Series({
        "voltage_v": 22.0,
        "current_a": 16.0,
        "temperature_c": 38.0,
        "power_w": 352.0,
        "dv_dt": -0.15,
        "dt_dt": 0.04,
        "est_r_int": 0.045
    })

    engine = FaultDiagnosisEngine()
    comparison = engine.compare_methods(rep, row)
    assert "physics_rule" in comparison
    assert "bayesian_evidential" in comparison
    assert comparison["physics_rule"].primary_failure_mode == FailureMode.PARASITIC_BUS_OVERLOAD.value
    assert comparison["bayesian_evidential"].primary_failure_mode == FailureMode.PARASITIC_BUS_OVERLOAD.value
