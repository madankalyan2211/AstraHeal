"""Shared infrastructure, baseline models, telemetry generators, and metrics for AstraHeal Paper 2."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    roc_auc_score,
    precision_recall_curve,
    auc,
    brier_score_loss,
)
from scipy.spatial.distance import mahalanobis
from scipy.special import softmax

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.anomaly.detector import AnomalyReport
from src.diagnosis.bayesian import BayesianEvidentialDiagnosticEngine
from src.diagnosis.rules import PhysicsRuleDiagnosticEngine
from src.diagnosis.schema import DiagnosisReport, DiagnosisStatus, FailureMode
from src.digital_twin.simulator import SpacecraftEPSDigitalTwin
from src.digital_twin.fault_injection import InjectedFaultSpec, FaultType


FEATURE_NAMES = ["voltage_v", "current_a", "temperature_c", "power_w", "dv_dt", "dt_dt", "est_r_int"]

KNOWN_CLASSES = [
    "NOMINAL_OPERATION",
    "BATTERY_INTERNAL_RESISTANCE_SPIKE",
    "SOLAR_ARRAY_STRING_FAULT",
    "THERMAL_RUNAWAY_INITIATION",
    "PARASITIC_BUS_OVERLOAD",
    "SENSOR_BIAS_DRIFT",
]

OOD_CLASSES = [
    "NOVEL_UNSEEN_MODE",
    "COMPOUND_CONCURRENT_FAULT",
    "EXTREME_THERMAL_INVERSION",
    "SENSOR_SIGN_INVERSION",
]


def generate_synthetic_telemetry_frame(
    class_name: str,
    noise_sigma: float = 0.0,
    rng: Optional[np.random.RandomState] = None
) -> Dict[str, float]:
    """Generate a single deterministic physics-consistent telemetry feature frame."""
    if rng is None:
        rng = np.random.RandomState(42)

    # Base physics archetypes for 28V spacecraft power system
    if class_name == "NOMINAL_OPERATION":
        v = rng.normal(28.2, 0.4)
        i = rng.normal(2.5, 0.3)
        t = rng.normal(22.0, 1.5)
        p = v * i
        dv = rng.normal(0.00, 0.005)
        dt = rng.normal(0.001, 0.002)
        r_int = rng.normal(0.045, 0.003)

    elif class_name == "BATTERY_INTERNAL_RESISTANCE_SPIKE":
        # Elevated internal impedance, high IR drop under load
        r_int = rng.normal(0.24, 0.03)
        i = rng.normal(7.5, 0.8)
        v = rng.normal(24.2, 0.6) - (r_int * i)
        t = rng.normal(32.0, 2.0)
        p = v * i
        dv = rng.normal(-0.06, 0.015)
        dt = rng.normal(0.025, 0.005)

    elif class_name == "SOLAR_ARRAY_STRING_FAULT":
        # Lost generation, system running off battery or low bus voltage during sunlight
        v = rng.normal(26.8, 0.5)
        i = rng.normal(3.8, 0.4)
        t = rng.normal(18.0, 1.5)
        p = rng.normal(105.0, 8.0)
        dv = rng.normal(-0.012, 0.004)
        dt = rng.normal(-0.006, 0.002)
        r_int = rng.normal(0.046, 0.004)

    elif class_name == "THERMAL_RUNAWAY_INITIATION":
        # Severe exothermic heating, rapid dT/dt, degrading voltage
        t = rng.normal(53.0, 2.5)
        dt = rng.normal(0.12, 0.02)
        v = rng.normal(24.5, 0.7)
        i = rng.normal(8.0, 0.9)
        p = v * i
        dv = rng.normal(-0.05, 0.012)
        r_int = rng.normal(0.075, 0.008)

    elif class_name == "PARASITIC_BUS_OVERLOAD":
        # Excessive load current dragging down voltage
        i = rng.normal(16.5, 1.2)
        v = rng.normal(21.5, 0.6)
        p = v * i
        t = rng.normal(36.0, 2.0)
        dv = rng.normal(-0.12, 0.025)
        dt = rng.normal(0.035, 0.006)
        r_int = rng.normal(0.048, 0.004)

    elif class_name == "SENSOR_BIAS_DRIFT":
        # Sensor offset without corresponding thermal or internal resistance change
        v = rng.normal(20.0, 0.5)
        i = rng.normal(2.5, 0.3)
        t = rng.normal(21.5, 1.2)
        p = rng.normal(80.0, 5.0)
        dv = rng.normal(0.00, 0.003)
        dt = rng.normal(0.00, 0.002)
        r_int = rng.normal(0.045, 0.003)

    # --- Out-of-Distribution Archetypes ---
    elif class_name == "NOVEL_UNSEEN_MODE":
        # Catastrophic bus short (500W load surge, collapse to 11V, severe negative dv/dt)
        v = rng.normal(11.2, 0.8)
        i = rng.normal(44.0, 2.5)
        t = rng.normal(42.0, 3.0)
        p = v * i
        dv = rng.normal(-6.5, 0.8)
        dt = rng.normal(0.25, 0.04)
        r_int = rng.normal(0.05, 0.01)

    elif class_name == "COMPOUND_CONCURRENT_FAULT":
        # Solar loss combined with exothermic thermal surge
        v = rng.normal(22.0, 0.8)
        i = rng.normal(12.5, 1.2)
        t = rng.normal(55.0, 2.5)
        p = rng.normal(275.0, 15.0)
        dv = rng.normal(-0.16, 0.03)
        dt = rng.normal(0.14, 0.025)
        r_int = rng.normal(0.18, 0.02)

    elif class_name == "EXTREME_THERMAL_INVERSION":
        # Deep eclipse cryogenic freeze (-55 deg C, impedance spike)
        t = rng.normal(-52.0, 3.0)
        dt = rng.normal(-0.18, 0.03)
        v = rng.normal(21.0, 0.7)
        i = rng.normal(1.2, 0.2)
        p = v * i
        dv = rng.normal(-0.08, 0.015)
        r_int = rng.normal(0.48, 0.05)

    elif class_name == "SENSOR_SIGN_INVERSION":
        # Wiring polarity flip (negative current during discharge)
        v = rng.normal(28.0, 0.5)
        i = rng.normal(-15.0, 1.0)
        t = rng.normal(22.0, 1.2)
        p = rng.normal(-420.0, 20.0)
        dv = rng.normal(0.01, 0.005)
        dt = rng.normal(0.002, 0.001)
        r_int = rng.normal(0.045, 0.003)

    else:
        raise ValueError(f"Unknown class name: {class_name}")

    # Additive relative sensor noise if requested
    if noise_sigma > 0.0:
        v += rng.normal(0.0, noise_sigma * 28.0)
        i += rng.normal(0.0, noise_sigma * 10.0)
        t += rng.normal(0.0, noise_sigma * 25.0)
        p += rng.normal(0.0, noise_sigma * 280.0)
        dv += rng.normal(0.0, noise_sigma * 0.1)
        dt += rng.normal(0.0, noise_sigma * 0.05)
        r_int += rng.normal(0.0, noise_sigma * 0.1)

    return {
        "voltage_v": float(v),
        "current_a": float(i),
        "temperature_c": float(t),
        "power_w": float(p),
        "dv_dt": float(dv),
        "dt_dt": float(dt),
        "est_r_int": float(max(0.001, r_int)),
        "class_label": class_name,
    }


def generate_benchmark_dataset(
    classes: List[str],
    samples_per_class: int = 200,
    noise_sigma: float = 0.0,
    seed: int = 42
) -> pd.DataFrame:
    """Generate a balanced multivariate telemetry dataset for specified classes."""
    rng = np.random.RandomState(seed)
    records = []
    for cls in classes:
        for _ in range(samples_per_class):
            rec = generate_synthetic_telemetry_frame(cls, noise_sigma=noise_sigma, rng=rng)
            records.append(rec)
    df = pd.DataFrame(records)
    return df


class StandardMahalanobisBaseline:
    """Centroid-based Mahalanobis distance classifier without evidential Dirichlet uncertainty."""

    def __init__(self, classes: List[str]):
        self.classes = classes
        self.centroids: Dict[str, np.ndarray] = {}
        self.cov_inv: Dict[str, np.ndarray] = {}

    def fit(self, X: np.ndarray, y: np.ndarray) -> StandardMahalanobisBaseline:
        for c in self.classes:
            X_c = X[y == c]
            if len(X_c) == 0:
                continue
            centroid = np.mean(X_c, axis=0)
            cov = np.cov(X_c, rowvar=False) + np.eye(X.shape[1]) * 1e-4
            self.centroids[c] = centroid
            self.cov_inv[c] = np.linalg.inv(cov)
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        all_probs = []
        for x in X:
            dists = []
            for c in self.classes:
                diff = x - self.centroids[c]
                d = np.sqrt(np.dot(np.dot(diff, self.cov_inv[c]), diff))
                dists.append(-d)
            probs = softmax(dists)
            all_probs.append(probs)
        return np.array(all_probs)

    def predict(self, X: np.ndarray) -> np.ndarray:
        probs = self.predict_proba(X)
        return np.array([self.classes[i] for i in np.argmax(probs, axis=1)])


class EvidentialDirichletWrapper:
    """Wrapper adapting the AstraHeal BayesianEvidentialDiagnosticEngine to standard benchmark APIs."""

    def __init__(self):
        self.engine = BayesianEvidentialDiagnosticEngine()
        self.classes = [
            "NOMINAL_OPERATION",
            "BATTERY_INTERNAL_RESISTANCE_SPIKE",
            "SOLAR_ARRAY_STRING_FAULT",
            "THERMAL_RUNAWAY_INITIATION",
            "PARASITIC_BUS_OVERLOAD",
            "SENSOR_BIAS_DRIFT",
        ]

    def predict_frame(self, row: pd.Series) -> DiagnosisReport:
        # Construct synthetic anomaly report based on distance from nominal
        v = float(row.get("voltage_v", 28.0))
        t = float(row.get("temperature_c", 22.0))
        r = float(row.get("est_r_int", 0.045))
        
        # Heuristic anomaly score
        is_nom = (27.0 <= v <= 29.5) and (t <= 30.0) and (r <= 0.07)
        anom_score = 0.08 if is_nom else 0.92
        
        rep = AnomalyReport(
            timestamp=0.0,
            anomaly_score=anom_score,
            is_anomaly=not is_nom,
            affected_signals=["voltage_v", "temperature_c"] if not is_nom else [],
            detector_name="Paper2Benchmark"
        )
        return self.engine.diagnose(rep, row)

    def predict_batch(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        preds = []
        confs = []
        epistemics = []
        aleatorics = []
        for _, row in df.iterrows():
            diag = self.predict_frame(row)
            preds.append(diag.primary_failure_mode)
            confs.append(diag.confidence)
            epistemics.append(diag.epistemic_uncertainty)
            aleatorics.append(diag.aleatoric_uncertainty)
        return np.array(preds), np.array(confs), np.array(epistemics), np.array(aleatorics)


class PhysicsRulesWrapper:
    """Wrapper adapting the AstraHeal PhysicsRuleDiagnosticEngine."""

    def __init__(self):
        self.engine = PhysicsRuleDiagnosticEngine()

    def predict_batch(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        preds = []
        confs = []
        for _, row in df.iterrows():
            v = float(row.get("voltage_v", 28.0))
            t = float(row.get("temperature_c", 22.0))
            r = float(row.get("est_r_int", 0.045))
            is_nom = (27.0 <= v <= 29.5) and (t <= 30.0) and (r <= 0.07)
            anom_score = 0.08 if is_nom else 0.92
            
            rep = AnomalyReport(
                timestamp=0.0,
                anomaly_score=anom_score,
                is_anomaly=not is_nom,
                affected_signals=["voltage_v", "temperature_c"] if not is_nom else [],
                detector_name="RulesBenchmark"
            )
            diag = self.engine.diagnose(rep, row)
            preds.append(diag.primary_failure_mode)
            confs.append(diag.confidence)
        return np.array(preds), np.array(confs)


def compute_expected_calibration_error(
    confs: np.ndarray,
    preds: np.ndarray,
    labels: np.ndarray,
    n_bins: int = 10
) -> float:
    """Compute Expected Calibration Error (ECE) with equal-width confidence binning."""
    accuracies = (preds == labels).astype(float)
    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n_total = len(confs)

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        mask = (confs > bin_lower) & (confs <= bin_upper)
        n_in_bin = np.sum(mask)
        if n_in_bin > 0:
            bin_acc = np.mean(accuracies[mask])
            bin_conf = np.mean(confs[mask])
            ece += (n_in_bin / n_total) * np.abs(bin_acc - bin_conf)

    return float(ece)


def evaluate_classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    confs: Optional[np.ndarray] = None,
    classes: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Compute comprehensive multiclass classification metrics."""
    acc = float(accuracy_score(y_true, y_pred))
    bal_acc = float(balanced_accuracy_score(y_true, y_pred))
    prec_macro, rec_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    
    unique_classes = classes or sorted(list(set(y_true) | set(y_pred)))
    prec_per, rec_per, f1_per, support_per = precision_recall_fscore_support(
        y_true, y_pred, labels=unique_classes, zero_division=0
    )
    
    per_class = {}
    for i, c in enumerate(unique_classes):
        per_class[c] = {
            "precision": float(prec_per[i]),
            "recall": float(rec_per[i]),
            "f1": float(f1_per[i]),
            "support": int(support_per[i]),
        }

    cm = confusion_matrix(y_true, y_pred, labels=unique_classes)

    res = {
        "accuracy": acc,
        "balanced_accuracy": bal_acc,
        "macro_precision": float(prec_macro),
        "macro_recall": float(rec_macro),
        "macro_f1": float(f1_macro),
        "per_class": per_class,
        "confusion_matrix": cm.tolist(),
        "classes": unique_classes,
    }

    if confs is not None:
        res["ece"] = compute_expected_calibration_error(confs, y_pred, y_true)
        res["mean_confidence"] = float(np.mean(confs))

    return res
