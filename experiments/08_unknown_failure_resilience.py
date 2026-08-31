"""Experiment 08: Unknown-Failure Resilience, Out-Of-Distribution (OOD) Detection & Uncertainty Calibration.

Evaluates:
- Epistemic uncertainty separation on known training conditions vs novel unseen anomalies
- Abstention rate on high-uncertainty scenarios
- Multi-fault simultaneous compounding failure handling
- Safe fallback execution vs aggressive action inhibition
"""

import sys
import json
from pathlib import Path

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.digital_twin.simulator import SpacecraftEPSDigitalTwin
from src.digital_twin.fault_injection import InjectedFaultSpec, FaultType
from src.telemetry.preprocess import TelemetryPreprocessor
from src.anomaly.detector import StatisticalDetector
from src.diagnosis.engine import FaultDiagnosisEngine
from src.diagnosis.schema import FailureMode, DiagnosisStatus
from src.diagnosis.resilience import UnknownFailureResilienceEvaluator
from src.planner.recovery_planner import AutonomousRecoveryPlanner


def run_experiment():
    print("=" * 75)
    print("ASTRAHEAL EXPERIMENT 08: Unknown-Failure Resilience & OOD Calibration")
    print("=" * 75)

    diag_engine = FaultDiagnosisEngine(primary_method="bayesian")
    resilience_evaluator = UnknownFailureResilienceEvaluator(max_epistemic_for_aggressive_action=0.50)

    # Benchmark test matrix: 3 Known vs 3 Unseen / Novel Scenarios
    test_cases = [
        # --- Known Conditions ---
        {
            "category": "KNOWN",
            "name": "Standard Battery Resistance Surge (4.0x)",
            "faults": [
                InjectedFaultSpec(fault_type=FaultType.BATTERY_RESISTANCE_SPIKE, start_time_sec=100.0, parameters={"resistance_multiplier": 4.0})
            ]
        },
        {
            "category": "KNOWN",
            "name": "Solar Array Partial String Shading (50%)",
            "faults": [
                InjectedFaultSpec(fault_type=FaultType.SOLAR_STRING_FAULT, start_time_sec=100.0, parameters={"remaining_health": 0.50})
            ]
        },
        {
            "category": "KNOWN",
            "name": "Exothermic Thermal Anomaly (60W Heat)",
            "faults": [
                InjectedFaultSpec(fault_type=FaultType.THERMAL_RUNAWAY, start_time_sec=100.0, parameters={"exothermic_heat_w": 60.0})
            ]
        },
        # --- Unseen / Out-Of-Distribution (OOD) Conditions ---
        {
            "category": "UNSEEN_OOD",
            "name": "Simultaneous Compound Fault (Solar Occlusion + Bus Short)",
            "faults": [
                InjectedFaultSpec(fault_type=FaultType.SOLAR_STRING_FAULT, start_time_sec=100.0, parameters={"remaining_health": 0.20}),
                InjectedFaultSpec(fault_type=FaultType.PARASITIC_LOAD_SURGE, start_time_sec=100.0, parameters={"extra_load_w": 250.0})
            ]
        },
        {
            "category": "UNSEEN_OOD",
            "name": "Extreme Novel Severity (15.0x Resistance Surge)",
            "faults": [
                InjectedFaultSpec(fault_type=FaultType.BATTERY_RESISTANCE_SPIKE, start_time_sec=100.0, parameters={"resistance_multiplier": 15.0})
            ]
        },
        {
            "category": "UNSEEN_OOD",
            "name": "Corrupted Sensor Inversion (Simultaneous Bias + Voltage Glitch)",
            "faults": [
                InjectedFaultSpec(fault_type=FaultType.SENSOR_BIAS_DRIFT, start_time_sec=100.0, parameters={"bias_offset": -12.0, "channel": "voltage_v"}),
                InjectedFaultSpec(fault_type=FaultType.SENSOR_BIAS_DRIFT, start_time_sec=100.0, parameters={"bias_offset": 25.0, "channel": "current_a"})
            ]
        }
    ]

    records = []
    print("\nExecuting Resilience & Uncertainty Benchmark Matrix:")
    print("=" * 100)
    print(f"{'Category':<12} | {'Scenario Name':<45} | {'Status':<16} | {'Epistemic':<10} | {'Aleatoric':<10} | {'Policy'}")
    print("=" * 100)

    epistemic_known, epistemic_ood = [], []
    aleatoric_known, aleatoric_ood = [], []

    for tc in test_cases:
        twin = SpacecraftEPSDigitalTwin(system_id="ASTRA-RESILIENCE", random_seed=42)
        for f in tc["faults"]:
            twin.inject_fault(f)

        # Run to fault steady state (300s)
        frames = [twin.step(dt_sec=10.0).to_dict() for _ in range(30)]
        df = pd.DataFrame(frames)
        preprocessor = TelemetryPreprocessor()
        feat_df = preprocessor.extract_features(df)

        detector = StatisticalDetector()
        detector.fit(feat_df.iloc[:5])
        rep = detector.detect_batch(feat_df)[-1]
        
        diag = diag_engine.diagnose_frame(rep, feat_df.iloc[-1])
        planner = AutonomousRecoveryPlanner()
        plan = planner.plan_recovery(twin, diag, horizon_sec=2000.0)

        profile = resilience_evaluator.evaluate_gating(diag, plan)

        policy_str = "SAFE_FALLBACK" if profile.safe_fallback_triggered else "AUTHORIZED"
        print(f"{tc['category']:<12} | {tc['name']:<45} | {diag.status.value:<16} | {diag.epistemic_uncertainty:<10.3f} | {diag.aleatoric_uncertainty:<10.3f} | {policy_str}")

        if tc["category"] == "KNOWN":
            epistemic_known.append(diag.epistemic_uncertainty)
            aleatoric_known.append(diag.aleatoric_uncertainty)
        else:
            epistemic_ood.append(diag.epistemic_uncertainty)
            aleatoric_ood.append(diag.aleatoric_uncertainty)

        records.append({
            "category": tc["category"],
            "scenario_name": tc["name"],
            "diagnosis_status": diag.status.value,
            "primary_failure_mode": diag.primary_failure_mode,
            "confidence": diag.confidence,
            "epistemic_uncertainty": diag.epistemic_uncertainty,
            "aleatoric_uncertainty": diag.aleatoric_uncertainty,
            "abstained_from_aggressive_action": profile.abstained_from_aggressive_action,
            "safe_fallback_triggered": profile.safe_fallback_triggered,
            "policy_rationale": profile.rationale
        })

    # Save results
    out_json = Path("evaluation/08_unknown_resilience_results.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    print(f"\n[✓] Results saved to: {out_json}")

    # Plot Epistemic vs Aleatoric Uncertainty Separation
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(epistemic_known, aleatoric_known, color="#2ca02c", s=150, edgecolors="black", label="Known In-Distribution Faults", zorder=5)
    ax.scatter(epistemic_ood, aleatoric_ood, color="#d62728", s=150, marker="^", edgecolors="black", label="Unseen / OOD Novel Conditions", zorder=5)

    ax.axvline(0.50, color="darkred", linestyle="--", alpha=0.7, label="Epistemic Gating Threshold (0.50)")
    ax.fill_betweenx([0, 1.0], 0.50, 1.05, color="red", alpha=0.1, label="Conservative Fallback Zone (Inhibit Aggressive Actions)")
    
    ax.set_xlabel("Epistemic Uncertainty ($u_{epistemic}$ — Model Ignorance / OOD Distance)", fontweight="bold")
    ax.set_ylabel("Aleatoric Uncertainty ($u_{aleatoric}$ — Multi-Hypothesis Entropy)", fontweight="bold")
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.set_title("AstraHeal Stage 10: Uncertainty Calibration & Out-of-Distribution Gating", fontweight="bold", fontsize=12)
    ax.legend(loc="upper left", frameon=True, fontsize=9)
    ax.grid(True, linestyle=":", alpha=0.5)

    plt.tight_layout()
    plot_path = Path("docs/figures/08_uncertainty_calibration_ood.png")
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[✓] Saved uncertainty calibration plot to: {plot_path}")

    print("\n[✓] Stage 10 Unknown-Failure Resilience Experiment Completed.")


if __name__ == "__main__":
    run_experiment()
