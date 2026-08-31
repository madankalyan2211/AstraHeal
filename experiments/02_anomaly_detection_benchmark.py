"""Experiment 02: Baseline Anomaly Detection Benchmark.

Compares:
1. Statistical Detector (Rolling Z-Score + Mahalanobis Distance)
2. Machine Learning Baseline: Isolation Forest
3. Machine Learning Baseline: One-Class SVM
4. Composite Ensemble Detector

Evaluates precision, recall, F1-score, false alarm rate, and detection latency.
"""

import sys
import json
from pathlib import Path

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import pandas as pd

from src.digital_twin.simulator import SpacecraftEPSDigitalTwin
from src.digital_twin.fault_injection import InjectedFaultSpec, FaultType
from src.anomaly.detector import (
    StatisticalDetector,
    IsolationForestDetector,
    OneClassSVMDetector,
    CompositeAnomalyDetector
)
from src.anomaly.evaluation import AnomalyEvaluator


def run_benchmark():
    print("=" * 70)
    print("ASTRAHEAL EXPERIMENT 02: Baseline Anomaly Detection Benchmark")
    print("=" * 70)

    # 1. Setup digital twin simulation with controlled fault injections
    sim = SpacecraftEPSDigitalTwin(system_id="ASTRA-BENCH-01", random_seed=42)
    
    # Fault 1: Battery Resistance Spike from t=4000 to t=5500
    sim.inject_fault(InjectedFaultSpec(
        fault_type=FaultType.BATTERY_RESISTANCE_SPIKE,
        start_time_sec=4000.0,
        duration_sec=1500.0,
        parameters={"resistance_multiplier": 3.8},
        description="Internal resistance surge"
    ))

    # Fault 2: Parasitic load surge from t=9000 to t=10500
    sim.inject_fault(InjectedFaultSpec(
        fault_type=FaultType.PARASITIC_LOAD_SURGE,
        start_time_sec=9000.0,
        duration_sec=1500.0,
        parameters={"extra_load_w": 180.0},
        description="Subsystem parasitic short"
    ))

    # Run simulation for ~2.5 orbits (14400s at 10s steps = 1440 frames)
    batch = sim.run_simulation(duration_sec=14400.0, dt_sec=10.0)
    df = batch.to_dataframe()

    # Ground truth: any interval where fault was active
    y_true = np.array([1 if row.get("meta_fault_active", False) else 0 for _, row in df.iterrows()])
    print(f"[+] Total simulation frames: {len(df)}")
    print(f"[+] Injected anomaly frames: {int(np.sum(y_true))} ({np.mean(y_true)*100:.1f}%)")

    # 2. Fit nominal window on initial 3000s
    nominal_df = df.iloc[:300]

    detectors = [
        StatisticalDetector(channels=["voltage_v", "current_a", "temperature_c"]),
        IsolationForestDetector(channels=["voltage_v", "current_a", "temperature_c"]),
        OneClassSVMDetector(channels=["voltage_v", "current_a", "temperature_c"]),
        CompositeAnomalyDetector()
    ]

    results = {}

    for det in detectors:
        det.fit(nominal_df)
        reports = det.detect_batch(df)
        metrics = AnomalyEvaluator.evaluate_with_ground_truth(reports, y_true, fault_onset_index=400)
        results[det.name] = metrics
        
        print(f"\n--- {det.name} ---")
        print(f"    Precision:          {metrics['precision']:.4f}")
        print(f"    Recall:             {metrics['recall']:.4f}")
        print(f"    F1 Score:           {metrics['f1_score']:.4f}")
        print(f"    False Alarm Rate:   {metrics['false_alarm_rate']:.4f}")
        if metrics['roc_auc'] is not None:
            print(f"    AUROC:              {metrics['roc_auc']:.4f}")
        print(f"    Detection Latency:  {metrics['detection_latency_steps']} steps ({metrics['detection_latency_steps']*10 if metrics['detection_latency_steps'] is not None else 0}s)")
        print(f"    Confusion Matrix:   {metrics['confusion_matrix']}")

    # Save benchmark results
    out_dir = Path("evaluation")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "anomaly_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n[✓] Benchmark results saved to: {out_dir / 'anomaly_benchmark_results.json'}")


if __name__ == "__main__":
    run_benchmark()
