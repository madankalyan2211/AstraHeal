"""Experiment 03: Fault Diagnosis and Uncertainty Estimation Verification.

Evaluates:
- Correct classification of known failure modes
- Rejection of nominal frames as INSUFFICIENT_EVIDENCE
- Detection of novel out-of-distribution faults as UNKNOWN_FAILURE
- Calibration of Epistemic (OOD distance) vs Aleatoric (Entropy) uncertainty
- Comparison between Physics Rules and Bayesian Evidential Inference
"""

import sys
import json
from pathlib import Path

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd
from src.anomaly.detector import AnomalyReport
from src.diagnosis.schema import FailureMode, DiagnosisStatus
from src.diagnosis.engine import FaultDiagnosisEngine


def run_experiment():
    print("=" * 70)
    print("ASTRAHEAL EXPERIMENT 03: Fault Diagnosis & Uncertainty Quantification")
    print("=" * 70)

    engine = FaultDiagnosisEngine()

    test_cases = [
        {
            "name": "Nominal Sunlight Operation",
            "report": AnomalyReport(timestamp=100.0, anomaly_score=0.08, is_anomaly=False, affected_signals=[], detector_name="Baseline"),
            "features": pd.Series({"voltage_v": 28.2, "current_a": 2.1, "temperature_c": 21.5, "power_w": 59.22, "dv_dt": 0.0, "dt_dt": 0.001, "est_r_int": 0.045, "subsystem": "EPS"}),
            "expected_status": DiagnosisStatus.INSUFFICIENT_EVIDENCE
        },
        {
            "name": "Battery Internal Resistance Spike",
            "report": AnomalyReport(timestamp=4200.0, anomaly_score=0.92, is_anomaly=True, affected_signals=["voltage_v", "temperature_c"], detector_name="Baseline"),
            "features": pd.Series({"voltage_v": 23.4, "current_a": 4.2, "temperature_c": 31.8, "power_w": 98.28, "dv_dt": -0.07, "dt_dt": 0.022, "est_r_int": 0.175, "subsystem": "EPS_BATTERY"}),
            "expected_status": DiagnosisStatus.KNOWN_FAILURE,
            "expected_mode": FailureMode.BATTERY_INTERNAL_RESISTANCE_SPIKE.value
        },
        {
            "name": "Thermal Runaway Initiation",
            "report": AnomalyReport(timestamp=6500.0, anomaly_score=0.98, is_anomaly=True, affected_signals=["temperature_c"], detector_name="Baseline"),
            "features": pd.Series({"voltage_v": 24.8, "current_a": 6.1, "temperature_c": 53.5, "power_w": 151.28, "dv_dt": -0.04, "dt_dt": 0.13, "est_r_int": 0.085, "subsystem": "EPS_THERMAL"}),
            "expected_status": DiagnosisStatus.KNOWN_FAILURE,
            "expected_mode": FailureMode.THERMAL_RUNAWAY_INITIATION.value
        },
        {
            "name": "Parasitic Bus Short / Overload",
            "report": AnomalyReport(timestamp=9200.0, anomaly_score=0.95, is_anomaly=True, affected_signals=["current_a", "voltage_v"], detector_name="Baseline"),
            "features": pd.Series({"voltage_v": 22.1, "current_a": 16.2, "temperature_c": 37.5, "power_w": 358.02, "dv_dt": -0.14, "dt_dt": 0.038, "est_r_int": 0.045, "subsystem": "EPS_DISTRIBUTION"}),
            "expected_status": DiagnosisStatus.KNOWN_FAILURE,
            "expected_mode": FailureMode.PARASITIC_BUS_OVERLOAD.value
        },
        {
            "name": "Novel Unseen Anomaly (Out-Of-Distribution)",
            "report": AnomalyReport(timestamp=12000.0, anomaly_score=0.99, is_anomaly=True, affected_signals=["voltage_v", "temperature_c", "current_a"], detector_name="Baseline"),
            "features": pd.Series({"voltage_v": 2.5, "current_a": -55.0, "temperature_c": -110.0, "power_w": -137.5, "dv_dt": -18.0, "dt_dt": -12.0, "est_r_int": 25.0, "subsystem": "EPS"}),
            "expected_status": DiagnosisStatus.UNKNOWN_FAILURE,
            "expected_mode": FailureMode.NOVEL_UNSEEN_ANOMALY.value
        }
    ]

    records = []
    print("\nExecuting diagnostic evaluations:")
    for tc in test_cases:
        diag = engine.diagnose_frame(tc["report"], tc["features"])
        rule_diag = engine.rule_engine.diagnose(tc["report"], tc["features"])
        
        print(f"\n[Case] {tc['name']}")
        print(f"  → Status:                {diag.status.value}")
        print(f"  → Primary Mode:          {diag.primary_failure_mode}")
        print(f"  → Confidence:            {diag.confidence:.3f}")
        print(f"  → Total Uncertainty:     {diag.uncertainty:.3f}")
        print(f"  → Epistemic (OOD) Unc:   {diag.epistemic_uncertainty:.3f}")
        print(f"  → Aleatoric (Entropy) Unc: {diag.aleatoric_uncertainty:.3f}")
        print(f"  → Evidence Count:        {len(diag.evidence)}")
        print(f"  → Rule Baseline Agree:   {rule_diag.primary_failure_mode == diag.primary_failure_mode}")

        records.append({
            "scenario": tc["name"],
            "status": diag.status.value,
            "primary_failure_mode": diag.primary_failure_mode,
            "confidence": diag.confidence,
            "total_uncertainty": diag.uncertainty,
            "epistemic_uncertainty": diag.epistemic_uncertainty,
            "aleatoric_uncertainty": diag.aleatoric_uncertainty,
            "evidence": diag.evidence
        })

    out_path = Path("evaluation/diagnosis_evaluation_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    print(f"\n[✓] Diagnosis evaluation results saved to: {out_path}")


if __name__ == "__main__":
    run_experiment()
