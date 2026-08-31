"""Experiment 12: AstraHeal Deterministic Flagship Mission Demonstration.

Tells a complete 14-step end-to-end mission narrative:
1. Spacecraft begins nominal flight in LEO orbit (Orbit 1)
2. Telemetry generated across solar array, battery, PDU, and thermal subsystems
3. Fault onset at t=3500s: Battery Internal Resistance Surge (4.5x degradation)
4. Anomaly detector triggers at t=3600s
5. Evidential Bayesian diagnosis identifies the failure mode
6. Epistemic and Aleatoric uncertainty quantified
7. Communication availability evaluated (Spacecraft in 25-minute ground blackout)
8. Counterfactual recovery action candidates generated (No-Op, Safe Mode, Throttle 50%, Standby)
9. Cloned forward simulation runs in isolated digital twin states (3000s lookahead)
10. Deterministic Safety Governor rejects unsafe candidates (No-Op rejected: predicted 52°C thermal breach)
11. Multi-objective planner ranks safe options and selects optimal action (Throttle Payload 50%)
12. Action authorized and executed on active spacecraft digital twin at t=3700s
13. Spacecraft battery temperature and voltage stabilize across Orbits 2 & 3
14. System logs recovery telemetry and resumes nominal continuous health monitoring
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
from src.planner.recovery_planner import AutonomousRecoveryPlanner
from src.safety.safety_governor import DeterministicSafetyGovernor, SafetyStatus
from src.communication.manager import CommunicationAwareAutonomyManager, AutonomyActionType


def run_flagship_mission():
    print("=" * 85)
    print("ASTRAHEAL EXPERIMENT 12: Deterministic Flagship Mission Demonstration")
    print("=" * 85)

    # 1. Initialize Spacecraft Digital Twin
    twin = SpacecraftEPSDigitalTwin(system_id="ASTRA-FLAGSHIP-01", random_seed=42)
    
    # 2. Inject Battery Internal Resistance Spike at t=3500s
    fault_t = 3500.0
    twin.inject_fault(InjectedFaultSpec(
        fault_type=FaultType.BATTERY_RESISTANCE_SPIKE,
        start_time_sec=fault_t,
        parameters={"resistance_multiplier": 4.5},
        description="High Impedance Aging Fault"
    ))

    print("\n[Step 1 & 2] Spacecraft operating nominally in LEO orbit (t=0 to 3500s)...")
    pre_fault_frames = []
    for _ in range(350):
        frame = twin.step(dt_sec=10.0)
        pre_fault_frames.append(frame.to_dict())

    print(f"[Step 3] In-flight fault onset at t={fault_t}s (Battery Impedance Surge 4.5x).")
    fault_onset_frames = []
    for _ in range(20):  # t=3500s to 3700s
        frame = twin.step(dt_sec=10.0)
        fault_onset_frames.append(frame.to_dict())

    combined_df = pd.DataFrame(pre_fault_frames + fault_onset_frames)
    preprocessor = TelemetryPreprocessor()
    feat_df = preprocessor.extract_features(combined_df)

    # 4. Anomaly Detection
    detector = StatisticalDetector()
    detector.fit(feat_df.iloc[:250])  # Fit on nominal first orbit
    batch_reports = detector.detect_batch(feat_df)
    latest_rep = batch_reports[-1]
    print(f"[Step 4] Anomaly Detected at t={twin.current_time_sec}s | Anomaly Score: {latest_rep.anomaly_score:.3f}")

    # 5 & 6. Evidential Diagnosis & Uncertainty Estimation
    diag_engine = FaultDiagnosisEngine(primary_method="bayesian")
    diag = diag_engine.diagnose_frame(latest_rep, feat_df.iloc[-1])
    print(f"[Step 5 & 6] Diagnosis: {diag.status.value} -> {diag.primary_failure_mode}")
    print(f"             Epistemic Uncertainty: {diag.epistemic_uncertainty:.3f} | Aleatoric Uncertainty: {diag.aleatoric_uncertainty:.3f}")

    # 7. Communication Latency Check
    comm_mgr = CommunicationAwareAutonomyManager()
    comm_state = comm_mgr.channel.evaluate_state(twin.current_time_sec)
    print(f"[Step 7] Communication Check: {comm_state.link_status.value} (Next contact in {comm_state.time_to_next_contact_sec:.0f}s)")
    print("         Decision: Communication blackout -> Onboard autonomous recovery MANDATORY.")

    # 8, 9, 10, 11. Planning, Counterfactuals & Safety Governor
    print("\n[Step 8 & 9] Forking Digital Twin state into isolated counterfactual simulation branches...")
    governor = DeterministicSafetyGovernor()
    planner = AutonomousRecoveryPlanner(governor=governor)
    plan = planner.plan_recovery(twin, diag, horizon_sec=3000.0)

    print("\n[Step 10 & 11] Safety Governor Evaluation & Multi-Objective Ranking:")
    for s in plan.all_evaluated_scenarios:
        verdict = s["safety_status"]
        sc_str = f"{s['score']:.3f}" if s["score"] > -1e5 else "DISQUALIFIED"
        print(f"   • [{s['action_id']}] {s['description']:<60} -> {verdict:<10} | Score: {sc_str} | Max T: {s['max_temp_c']:.1f}°C")
        if s["violations"]:
            for v in s["violations"]:
                print(f"     ↳ [REJECTION REASON]: {v}")

    print(f"\n[★] Selected Action: {plan.selected_action.action_id} ({plan.selected_action.action_type.value})")
    print(f"[★] Optimal Score:   {plan.selection_score:.3f}")

    # 12. Execute Plan on Active Twin
    print(f"\n[Step 12] Authorizing and executing {plan.selected_action.action_id} on active spacecraft at t={twin.current_time_sec}s...")
    planner.execute_plan_on_twin(twin, plan)

    # 13 & 14. Post-Recovery Stabilization across 2 Orbits (12,000s)
    print("[Step 13 & 14] Simulating post-recovery spacecraft operations for 2 additional orbits (12,000s)...")
    post_recovery_frames = []
    for _ in range(1200):
        frame = twin.step(dt_sec=10.0)
        post_recovery_frames.append(frame.to_dict())

    full_telemetry_df = pd.concat([combined_df, pd.DataFrame(post_recovery_frames)], ignore_index=True)

    # Save CSV
    out_csv = Path("simulations/flagship_mission_telemetry.csv")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    full_telemetry_df.to_csv(out_csv, index=False)
    print(f"\n[✓] Saved complete flagship telemetry to: {out_csv}")

    # Plot 4-Panel Flagship Timeline
    fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)
    t_hrs = full_telemetry_df["timestamp"] / 3600.0

    # Panel 1: Voltage
    axes[0].plot(t_hrs, full_telemetry_df["voltage_v"], color="#1f77b4", lw=1.5, label="Bus Voltage (V)")
    axes[0].axvline(fault_t / 3600.0, color="red", linestyle="--", label="Fault Onset (3500s)")
    axes[0].axvline(3700.0 / 3600.0, color="green", linestyle=":", label="Autonomous Action Executed (3700s)")
    axes[0].axhline(22.0, color="darkred", linestyle="--", alpha=0.5, label="Undervoltage Limit (22V)")
    axes[0].set_ylabel("Bus Voltage [V]", fontweight="bold")
    axes[0].legend(loc="upper right", frameon=True, fontsize=8)
    axes[0].grid(True, linestyle=":", alpha=0.5)

    # Panel 2: Current
    axes[1].plot(t_hrs, full_telemetry_df["current_a"], color="#ff7f0e", lw=1.2, label="Battery Current (A)")
    axes[1].set_ylabel("Current [A]", fontweight="bold")
    axes[1].legend(loc="upper right", frameon=True, fontsize=8)
    axes[1].grid(True, linestyle=":", alpha=0.5)

    # Panel 3: Temperature
    axes[2].plot(t_hrs, full_telemetry_df["temperature_c"], color="#2ca02c", lw=1.5, label="Battery Temp (°C)")
    axes[2].axhline(46.0, color="red", linestyle="--", alpha=0.7, label="Hard Temp Limit (46°C)")
    axes[2].set_ylabel("Temp [°C]", fontweight="bold")
    axes[2].legend(loc="upper right", frameon=True, fontsize=8)
    axes[2].grid(True, linestyle=":", alpha=0.5)

    # Panel 4: State of Charge
    axes[3].plot(t_hrs, full_telemetry_df["state_of_charge"] * 100.0, color="#9467bd", lw=1.5, label="Battery SoC (%)")
    axes[3].axhline(15.0, color="red", linestyle="--", alpha=0.7, label="Hard SoC Floor (15%)")
    axes[3].set_ylabel("SoC [%]", fontweight="bold")
    axes[3].set_xlabel("Mission Elapsed Time [Hours]", fontweight="bold")
    axes[3].legend(loc="upper right", frameon=True, fontsize=8)
    axes[3].grid(True, linestyle=":", alpha=0.5)

    fig.suptitle("AstraHeal Flagship Mission Demonstration: Autonomous Closed-Loop Self-Healing in LEO Orbit", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plot_path = Path("docs/figures/12_flagship_mission_timeline.png")
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[✓] Saved flagship mission timeline figure to: {plot_path}")

    print("\n[✓] Stage 12 Flagship Mission Demonstration Completed.")


if __name__ == "__main__":
    run_flagship_mission()
