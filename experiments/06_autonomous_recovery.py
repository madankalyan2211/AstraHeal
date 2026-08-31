"""Experiment 06: End-to-End Autonomous Recovery Planning with Deterministic Safety Governor Gating.

Demonstrates:
1. In-flight fault onset during orbital mission
2. Autonomous Anomaly Detection & Evidential Diagnosis
3. Counterfactual lookahead across candidate branches
4. Deterministic hard-constraint enforcement by the Safety Governor
5. Optimal soft-objective ranking
6. Real-time execution of the authorized safe recovery plan on the active twin
7. Closed-loop recovery verification over subsequent orbits
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


def run_experiment():
    print("=" * 75)
    print("ASTRAHEAL EXPERIMENT 06: Autonomous Recovery Planning & Safety Governor")
    print("=" * 75)

    # 1. Start primary spacecraft simulation
    twin = SpacecraftEPSDigitalTwin(system_id="ASTRA-SC-01", random_seed=42)

    # 2. Inject Critical Battery Impedance Fault at t=4000s
    fault_t = 4000.0
    twin.inject_fault(InjectedFaultSpec(
        fault_type=FaultType.BATTERY_RESISTANCE_SPIKE,
        start_time_sec=fault_t,
        parameters={"resistance_multiplier": 5.0},
        description="Critical Cell Impedance Degradation"
    ))

    print(f"[+] Initializing spacecraft in LEO orbit. Simulating to fault at t={fault_t}s...")
    history_frames = []
    
    # Run up to t=4300s (300s into fault)
    for _ in range(430):
        frame = twin.step(dt_sec=10.0)
        history_frames.append(frame.to_dict())

    history_df = pd.DataFrame(history_frames)
    preprocessor = TelemetryPreprocessor()
    feat_df = preprocessor.extract_features(history_df)

    # 3. Anomaly Detection
    detector = StatisticalDetector()
    detector.fit(feat_df.iloc[:300])  # Fit on first nominal orbit
    reports = detector.detect_batch(feat_df)
    latest_rep = reports[-1]
    print(f"[+] Fault Detected at t={twin.current_time_sec}s | Anomaly Score: {latest_rep.anomaly_score:.3f}")
    print(f"    Affected Signals: {latest_rep.affected_signals}")

    # 4. Fault Diagnosis
    diag_engine = FaultDiagnosisEngine(primary_method="bayesian")
    diag = diag_engine.diagnose_frame(latest_rep, feat_df.iloc[-1])
    print(f"[+] Diagnosis Verdict: {diag.status.value} -> {diag.primary_failure_mode}")
    print(f"    Confidence: {diag.confidence:.3f} | Epistemic Uncertainty: {diag.epistemic_uncertainty:.3f}")

    # 5. Autonomous Recovery Planner & Safety Governor
    governor = DeterministicSafetyGovernor()
    planner = AutonomousRecoveryPlanner(governor=governor)
    
    print("\n[+] Running Counterfactual Lookahead & Safety Governor Evaluation...")
    plan = planner.plan_recovery(twin, diag, horizon_sec=6000.0)

    print("\n" + "=" * 95)
    print(f"{'Action ID':<25} | {'Type':<22} | {'Governor Verdict':<18} | {'Score':<8} | {'Max Temp':<9}")
    print("=" * 95)

    for s in plan.all_evaluated_scenarios:
        verdict = s["safety_status"]
        sc_str = f"{s['score']:.3f}" if s["score"] > -1e5 else "DISQUALIFIED"
        print(f"{s['action_id']:<25} | {s['action_type']:<22} | {verdict:<18} | {sc_str:<8} | {s['max_temp_c']:>6.1f}°C")
        if s["violations"]:
            for v in s["violations"]:
                print(f"   ↳ [REJECTION REASON]: {v}")

    print("=" * 95)
    print(f"[★] Selected Action: {plan.selected_action.action_id} ({plan.selected_action.action_type.value})")
    print(f"[★] Selection Score: {plan.selection_score:.3f}")
    print("[★] Decision Rationale:")
    for r in plan.decision_rationale:
        print(f"    • {r}")

    # 6. Apply Approved Action to Active Twin and Simulate 2 Subsequent Orbits
    print("\n[+] Authorizing and applying selected recovery action to active spacecraft...")
    planner.execute_plan_on_twin(twin, plan)

    post_recovery_frames = []
    print("[+] Simulating post-recovery spacecraft operations for 2 additional orbits (12,000s)...")
    for _ in range(1200):
        frame = twin.step(dt_sec=10.0)
        post_recovery_frames.append(frame.to_dict())

    full_mission_df = pd.concat([history_df, pd.DataFrame(post_recovery_frames)], ignore_index=True)

    # 7. Multi-Panel Recovery Trajectory Plot
    fig, axes = plt.subplots(4, 1, figsize=(13, 10), sharex=True)
    t_hrs = full_mission_df["timestamp"] / 3600.0

    # Panel 1: Voltage
    axes[0].plot(t_hrs, full_mission_df["voltage_v"], color="#1f77b4", lw=1.5, label="Bus Voltage (V)")
    axes[0].axvline(fault_t / 3600.0, color="red", linestyle="--", label="Fault Injected (4000s)")
    axes[0].axvline(4300.0 / 3600.0, color="green", linestyle=":", label="Autonomous Action Executed (4300s)")
    axes[0].axhline(22.0, color="darkred", linestyle="--", alpha=0.5, label="Undervoltage Limit (22V)")
    axes[0].set_ylabel("Voltage [V]", fontweight="bold")
    axes[0].legend(loc="upper right", frameon=True, fontsize=8)
    axes[0].grid(True, linestyle=":", alpha=0.5)

    # Panel 2: Current
    axes[1].plot(t_hrs, full_mission_df["current_a"], color="#ff7f0e", lw=1.2, label="Current (A)")
    axes[1].set_ylabel("Current [A]", fontweight="bold")
    axes[1].legend(loc="upper right", frameon=True, fontsize=8)
    axes[1].grid(True, linestyle=":", alpha=0.5)

    # Panel 3: Temperature
    axes[2].plot(t_hrs, full_mission_df["temperature_c"], color="#2ca02c", lw=1.5, label="Battery Temp (°C)")
    axes[2].axhline(46.0, color="red", linestyle="--", alpha=0.7, label="Hard Temp Limit (46°C)")
    axes[2].set_ylabel("Temp [°C]", fontweight="bold")
    axes[2].legend(loc="upper right", frameon=True, fontsize=8)
    axes[2].grid(True, linestyle=":", alpha=0.5)

    # Panel 4: State of Charge
    axes[3].plot(t_hrs, full_mission_df["state_of_charge"] * 100.0, color="#9467bd", lw=1.5, label="Battery SoC (%)")
    axes[3].axhline(15.0, color="red", linestyle="--", alpha=0.7, label="Hard SoC Reserve Floor (15%)")
    axes[3].set_ylabel("SoC [%]", fontweight="bold")
    axes[3].set_xlabel("Mission Elapsed Time [Hours]", fontweight="bold")
    axes[3].legend(loc="upper right", frameon=True, fontsize=8)
    axes[3].grid(True, linestyle=":", alpha=0.5)

    fig.suptitle("AstraHeal Stage 8: Autonomous Fault Recovery & Post-Intervention Stabilization", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plot_path = Path("docs/figures/06_autonomous_recovery_plan.png")
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[✓] Saved recovery trajectory plot to: {plot_path}")

    # Save summary results
    out_path = Path("evaluation/06_autonomous_recovery_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(plan.model_dump(), f, indent=2)
    print(f"[✓] Saved plan output to: {out_path}")

    print("\n[✓] Stage 8 Autonomous Recovery Planning Experiment Complete.")


if __name__ == "__main__":
    run_experiment()
