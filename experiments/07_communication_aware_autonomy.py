"""Experiment 07: Communication-Aware Autonomy and Ground Delay Arbitration.

Evaluates:
- Real-time ground pass visibility vs communication blackout
- Arbitration between ACT_AUTONOMOUSLY and WAIT_FOR_GROUND
- Time-to-criticality vs Ground contact latency budget
- Autonomous intervention precision and deferred telemetry logging
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

from src.communication.channel import CommunicationChannel, LinkStatus
from src.communication.manager import CommunicationAwareAutonomyManager, AutonomyActionType
from src.digital_twin.simulator import SpacecraftEPSDigitalTwin
from src.digital_twin.fault_injection import InjectedFaultSpec, FaultType
from src.telemetry.preprocess import TelemetryPreprocessor
from src.anomaly.detector import StatisticalDetector
from src.diagnosis.engine import FaultDiagnosisEngine
from src.planner.recovery_planner import AutonomousRecoveryPlanner


def run_experiment():
    print("=" * 75)
    print("ASTRAHEAL EXPERIMENT 07: Communication-Aware Autonomy Arbitration")
    print("=" * 75)

    # 1. Setup Communication Channel & Manager
    channel = CommunicationChannel(orbit_period_sec=5740.0, pass_duration_sec=600.0)
    comm_mgr = CommunicationAwareAutonomyManager(channel=channel, ground_operator_decision_latency_sec=300.0)

    # Test Scenarios
    scenarios = [
        {
            "id": "SCEN-01-CRITICAL-BLACKOUT",
            "name": "Fast Thermal Runaway in Communication Blackout",
            "time_sec": 800.0,  # Deep in blackout (next pass at ~2300s)
            "fault_type": FaultType.THERMAL_RUNAWAY,
            "fault_params": {"exothermic_heat_w": 130.0},
            "expected": AutonomyActionType.ACT_AUTONOMOUSLY
        },
        {
            "id": "SCEN-02-BENIGN-BLACKOUT",
            "name": "Gradual Solar String Fade in Blackout",
            "time_sec": 1800.0,  # Near end of blackout (next pass in 500s)
            "fault_type": FaultType.SOLAR_STRING_FAULT,
            "fault_params": {"remaining_health": 0.65},
            "expected": AutonomyActionType.WAIT_FOR_GROUND
        },
        {
            "id": "SCEN-03-ACTIVE-PASS-URGENT",
            "name": "Catastrophic Short During Active Ground Pass",
            "time_sec": 2400.0,  # Ground pass active!
            "fault_type": FaultType.PARASITIC_LOAD_SURGE,
            "fault_params": {"extra_load_w": 300.0},
            "expected": AutonomyActionType.ACT_AUTONOMOUSLY
        },
        {
            "id": "SCEN-04-ACTIVE-PASS-STABLE",
            "name": "Minor Sensor Bias During Active Ground Pass",
            "time_sec": 2500.0,  # Ground pass active!
            "fault_type": FaultType.SENSOR_BIAS_DRIFT,
            "fault_params": {"bias_offset": -2.0},
            "expected": AutonomyActionType.WAIT_FOR_GROUND
        }
    ]

    results = []
    print("\nExecuting Communication-Aware Arbitration Matrix:")

    for sc in scenarios:
        t = sc["time_sec"]
        twin = SpacecraftEPSDigitalTwin(system_id="ASTRA-COMM-SC", random_seed=42)
        twin.inject_fault(InjectedFaultSpec(
            fault_type=sc["fault_type"],
            start_time_sec=max(0.0, t - 100.0),
            parameters=sc["fault_params"]
        ))
        
        # Step twin to scenario timestamp
        for _ in range(int(t / 10.0)):
            twin.step(dt_sec=10.0)

        # Telemetry & Diagnosis
        diag_engine = FaultDiagnosisEngine()
        rep = StatisticalDetector().fit(pd.DataFrame([twin.step(1.0).to_dict() for _ in range(10)])).detect_frame(twin.step(1.0).to_dict())
        diag = diag_engine.diagnose_frame(rep, pd.Series(twin.step(1.0).to_dict()))

        # Recovery Planner
        planner = AutonomousRecoveryPlanner()
        plan = planner.plan_recovery(twin, diag, horizon_sec=3000.0)
        
        # Identify No-Op Scenario
        noop_scen = next((s for s in planner.simulator.evaluate_all(twin, [plan.selected_action]) if s), None)

        # Communication Arbitration
        decision = comm_mgr.arbitrate(
            current_time_sec=t,
            diagnosis=diag,
            plan=plan,
            noop_scenario=noop_scen
        )

        print(f"\n[Scenario] {sc['name']} (t={t}s)")
        print(f"  • Link Status:       {decision.link_status.value}")
        print(f"  • Time to Contact:   {decision.time_to_ground_contact_sec:.1f}s")
        print(f"  • Time to Critical:  {decision.time_to_criticality_sec:.1f}s")
        print(f"  • Verdict:           {decision.decision.value} (Expected: {sc['expected'].value})")
        print(f"  • Rationale:         {decision.rationale}")

        results.append({
            "scenario_id": sc["id"],
            "name": sc["name"],
            "timestamp": t,
            "link_status": decision.link_status.value,
            "time_to_contact_sec": decision.time_to_ground_contact_sec,
            "time_to_criticality_sec": decision.time_to_criticality_sec,
            "arbitrated_decision": decision.decision.value,
            "rationale": decision.rationale
        })

    # Save results
    out_path = Path("evaluation/07_communication_autonomy_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[✓] Results saved to: {out_path}")

    # Plot Ground Pass Visibility & Autonomy Timeline
    fig, ax = plt.subplots(figsize=(12, 5))
    times = np.arange(0, 12000, 20.0)
    in_pass = []
    for tm in times:
        st = channel.evaluate_state(tm)
        in_pass.append(1 if st.link_status == LinkStatus.IN_CONTACT else 0)

    ax.fill_between(times / 3600.0, 0, in_pass, color="#2ca02c", alpha=0.3, label="Ground Station Contact Pass (Svalbard/White Sands)")
    
    # Mark scenario decision events
    for sc in scenarios:
        t_hr = sc["time_sec"] / 3600.0
        col = "red" if sc["expected"] == AutonomyActionType.ACT_AUTONOMOUSLY else "blue"
        ax.scatter(t_hr, 0.5, color=col, s=120, zorder=5, edgecolors="black")
        ax.text(t_hr, 0.65, sc["id"], rotation=25, fontsize=8, fontweight="bold", ha="center")

    ax.set_yticks([0, 1])
    ax.set_yticklabels(["Communication Blackout", "Active Ground Link"], fontweight="bold")
    ax.set_xlabel("Mission Elapsed Time [Hours]", fontweight="bold")
    ax.set_title("AstraHeal Stage 9: Communication Visibility Windows & Autonomous Arbitration Events", fontweight="bold", fontsize=12)
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle=":", alpha=0.5)

    plt.tight_layout()
    plot_path = Path("docs/figures/07_communication_autonomy_timeline.png")
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[✓] Saved arbitration timeline plot to: {plot_path}")

    print("\n[✓] Stage 9 Communication-Aware Autonomy Experiment Complete.")


if __name__ == "__main__":
    run_experiment()
