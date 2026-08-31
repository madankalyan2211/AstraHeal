"""Experiment 04: Full Multi-Orbit Mission Simulation with Autonomous Closed-Loop Diagnosis.

Integrates Stages 1 through 6:
1. Spacecraft Power-System Digital Twin Simulation (3 Orbits, LEO)
2. Reproducible Fault Injections (Solar loss, Battery degradation, Bus overload)
3. Standardized Telemetry Generation
4. Telemetry Preprocessing & Feature Extraction
5. Anomaly Detection Pipeline
6. Bayesian Evidential Fault Diagnosis with Epistemic/Aleatoric Uncertainty Quantification
"""

import sys
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
from src.diagnosis.schema import DiagnosisStatus


def run_mission_simulation():
    print("=" * 70)
    print("ASTRAHEAL EXPERIMENT 04: Spacecraft EPS Digital Twin Closed-Loop Mission")
    print("=" * 70)

    # 1. Initialize Spacecraft EPS Digital Twin
    twin = SpacecraftEPSDigitalTwin(system_id="ASTRA-SC-01", random_seed=42)

    # Inject realistic space mission fault sequence across 3 orbits (18000s)
    # Orbit period = 5740s.
    # Fault 1: Solar panel string failure at t=4200s (Orbit 1 sunlight phase)
    twin.inject_fault(InjectedFaultSpec(
        fault_type=FaultType.SOLAR_STRING_FAULT,
        start_time_sec=4200.0,
        duration_sec=2000.0,
        severity=0.7,
        parameters={"remaining_health": 0.35},
        description="Solar Array Partial String Occlusion"
    ))

    # Fault 2: Battery internal resistance surge at t=8500s (Orbit 2 eclipse discharge phase)
    twin.inject_fault(InjectedFaultSpec(
        fault_type=FaultType.BATTERY_RESISTANCE_SPIKE,
        start_time_sec=8500.0,
        duration_sec=1500.0,
        parameters={"resistance_multiplier": 3.5},
        description="Battery Inter-Cell Impedance Degradation"
    ))

    # Fault 3: Parasitic load short at t=14000s (Orbit 3)
    twin.inject_fault(InjectedFaultSpec(
        fault_type=FaultType.PARASITIC_LOAD_SURGE,
        start_time_sec=14000.0,
        duration_sec=1200.0,
        parameters={"extra_load_w": 160.0},
        description="PDU Subsystem Short Overload"
    ))

    print("[+] Simulating 3 LEO orbits (~18,000 seconds / 5 hours mission time at 10s steps)...")
    sim_file = Path("simulations/mission_run_3orbits.csv")
    sim_file.parent.mkdir(parents=True, exist_ok=True)
    batch = twin.run_simulation(duration_sec=18000.0, dt_sec=10.0, output_csv_path=sim_file)
    print(f"[+] Raw simulation frames generated: {len(batch)} -> Saved to {sim_file}")

    # 2. Telemetry Preprocessing & Feature Extraction
    preprocessor = TelemetryPreprocessor(processed_dir="data/processed")
    feat_df, _ = preprocessor.process_and_save(sim_file, "mission_run_3orbits_processed.csv")
    print(f"[+] Preprocessed telemetry shape: {feat_df.shape}")

    # 3. Anomaly Detection
    detector = StatisticalDetector()
    # Fit on first complete nominal orbit (first 574 samples = 5740s) to learn day/night transitions
    detector.fit(feat_df.iloc[:574])
    anomaly_reports = detector.detect_batch(feat_df)
    anom_count = sum(1 for r in anomaly_reports if r.is_anomaly)
    print(f"[+] Anomaly Detection: {anom_count} / {len(anomaly_reports)} frames triggered ({anom_count/len(anomaly_reports)*100:.1f}%)")

    # 4. Fault Diagnosis & Uncertainty Quantification
    diag_engine = FaultDiagnosisEngine(primary_method="bayesian")
    diag_reports = diag_engine.diagnose_batch(anomaly_reports, feat_df)

    # Summarize diagnostic decisions
    status_counts = {}
    mode_counts = {}
    for d in diag_reports:
        status_counts[d.status.value] = status_counts.get(d.status.value, 0) + 1
        if d.status == DiagnosisStatus.KNOWN_FAILURE:
            mode_counts[d.primary_failure_mode] = mode_counts.get(d.primary_failure_mode, 0) + 1

    print("\n[+] Autonomous Diagnostic Summary:")
    for st, count in status_counts.items():
        print(f"    {st:25s}: {count:5d} frames")
    print("\n    Known Failure Modes Identified:")
    for mode, count in mode_counts.items():
        print(f"      • {mode:35s}: {count:4d} frames")

    # 5. Publication-Quality Multi-Panel Mission Visualizer
    fig, axes = plt.subplots(5, 1, figsize=(14, 12), sharex=True)
    t = feat_df["timestamp"] / 3600.0  # Hours

    # Panel 1: Voltage and Current
    ax1 = axes[0]
    ax1.plot(t, feat_df["voltage_v"], color="#1f77b4", lw=1.5, label="Bus Voltage (V)")
    ax1.set_ylabel("Voltage [V]", fontweight="bold", color="#1f77b4")
    ax1.tick_params(axis="y", labelcolor="#1f77b4")
    ax1_twin = ax1.twinx()
    ax1_twin.plot(t, feat_df["current_a"], color="#ff7f0e", lw=1.2, alpha=0.85, label="Current (A)")
    ax1_twin.set_ylabel("Current [A]", fontweight="bold", color="#ff7f0e")
    ax1_twin.tick_params(axis="y", labelcolor="#ff7f0e")
    ax1.set_title("AstraHeal Autonomous Closed-Loop Telemetry & Diagnostic Trajectory", fontweight="bold", fontsize=13)
    ax1.grid(True, linestyle=":", alpha=0.5)

    # Panel 2: Solar Generation vs Total Load Power
    ax2 = axes[1]
    if "meta_solar_power_w" in feat_df.columns:
        ax2.plot(t, feat_df["meta_solar_power_w"], color="#2ca02c", lw=1.5, label="Solar Generation (W)")
    if "meta_load_power_w" in feat_df.columns:
        ax2.plot(t, feat_df["meta_load_power_w"], color="#d62728", lw=1.5, label="Spacecraft Load Demand (W)")
    ax2.set_ylabel("Power [W]", fontweight="bold")
    ax2.legend(loc="upper right", frameon=True)
    ax2.grid(True, linestyle=":", alpha=0.5)

    # Panel 3: Battery Temperature & State of Charge
    ax3 = axes[2]
    ax3.plot(t, feat_df["temperature_c"], color="#9467bd", lw=1.5, label="Core Temp (°C)")
    ax3.set_ylabel("Temp [°C]", fontweight="bold", color="#9467bd")
    ax3.tick_params(axis="y", labelcolor="#9467bd")
    ax3_twin = ax3.twinx()
    ax3_twin.plot(t, feat_df["state_of_charge"] * 100.0, color="#8c564b", lw=1.2, linestyle="--", label="SoC (%)")
    ax3_twin.set_ylabel("SoC [%]", fontweight="bold", color="#8c564b")
    ax3_twin.tick_params(axis="y", labelcolor="#8c564b")
    ax3.grid(True, linestyle=":", alpha=0.5)

    # Panel 4: Anomaly Scores & Threshold
    ax4 = axes[3]
    anom_scores = [r.anomaly_score for r in anomaly_reports]
    ax4.plot(t, anom_scores, color="#e377c2", lw=1.5, label="Anomaly Score")
    ax4.axhline(0.5, color="red", linestyle="--", alpha=0.7, label="Anomaly Threshold (0.5)")
    ax4.set_ylabel("Anomaly Score", fontweight="bold")
    ax4.set_ylim(-0.05, 1.05)
    ax4.legend(loc="upper right", frameon=True)
    ax4.grid(True, linestyle=":", alpha=0.5)

    # Panel 5: Diagnostic Confidence and Epistemic Uncertainty
    ax5 = axes[4]
    confidences = [d.confidence if d.status == DiagnosisStatus.KNOWN_FAILURE else 0.0 for d in diag_reports]
    epistemic_uncs = [d.epistemic_uncertainty for d in diag_reports]
    ax5.plot(t, confidences, color="#17becf", lw=1.5, label="Known Diagnosis Confidence")
    ax5.plot(t, epistemic_uncs, color="#bcbd22", lw=1.2, linestyle="-.", label="Epistemic Uncertainty (OOD)")
    ax5.set_ylabel("Confidence / Uncertainty", fontweight="bold")
    ax5.set_xlabel("Elapsed Mission Time [Hours]", fontweight="bold")
    ax5.set_ylim(-0.05, 1.05)
    ax5.legend(loc="upper right", frameon=True)
    ax5.grid(True, linestyle=":", alpha=0.5)

    plt.tight_layout()
    plot_path = Path("docs/figures/04_closed_loop_mission_trajectory.png")
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[+] Saved multi-panel mission plot: {plot_path}")

    print("\n[✓] Stage 1 through 6 End-to-End Simulation & Verification Complete.")


if __name__ == "__main__":
    run_mission_simulation()
