"""Experiment 05: Counterfactual Mission Simulation and Recovery Branching.

Demonstrates:
1. Mission execution up to fault onset
2. Autonomous Anomaly Detection & Fault Diagnosis
3. Generation of physically meaningful candidate recovery actions
4. Isolated branching in cloned Digital Twins (0% mutation of primary state)
5. Multi-scenario comparative evaluation & risk metric profiling
6. Publication-grade multi-branch visualization
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
from src.anomaly.detector import StatisticalDetector
from src.diagnosis.engine import FaultDiagnosisEngine
from src.diagnosis.schema import FailureMode
from src.planner.actions import ActionGenerator, RecoveryActionType
from src.planner.counterfactual import CounterfactualSimulator


def run_experiment():
    print("=" * 75)
    print("ASTRAHEAL EXPERIMENT 05: Counterfactual Mission Simulation & Branching")
    print("=" * 75)

    # 1. Start primary mission digital twin
    twin = SpacecraftEPSDigitalTwin(system_id="ASTRA-SC-01", random_seed=42)

    # 2. Inject fault: Battery Internal Resistance Surge at t=500s (during Eclipse discharge)
    fault_onset_t = 500.0
    twin.inject_fault(InjectedFaultSpec(
        fault_type=FaultType.BATTERY_RESISTANCE_SPIKE,
        start_time_sec=fault_onset_t,
        parameters={"resistance_multiplier": 4.5},
        description="High Impedance Degradation"
    ))

    # Run primary twin up to fault onset + 300s (step to t=800s in eclipse)
    print(f"[+] Simulating mission forward to fault event at t={fault_onset_t}s...")
    history_frames = []
    for _ in range(80):
        frame = twin.step(dt_sec=10.0)
        history_frames.append(frame.to_dict())

    history_df = pd.DataFrame(history_frames)

    # 3. Preprocess Telemetry and Extract Features
    from src.telemetry.preprocess import TelemetryPreprocessor
    preprocessor = TelemetryPreprocessor()
    feat_df = preprocessor.extract_features(history_df)

    # 4. Detect Anomaly
    detector = StatisticalDetector()
    detector.fit(feat_df.iloc[:30])  # Fit on nominal pre-fault eclipse frames
    batch_reports = detector.detect_batch(feat_df)
    rep = batch_reports[-1]
    print(f"[+] Telemetry at t={twin.current_time_sec}s -> Anomaly Score: {rep.anomaly_score:.3f} | Trigger: {rep.is_anomaly}")
    print(f"    Affected Signals: {rep.affected_signals}")

    # 5. Diagnose Fault
    diag_engine = FaultDiagnosisEngine(primary_method="bayesian")
    diag = diag_engine.diagnose_frame(rep, feat_df.iloc[-1])
    print(f"[+] Diagnosis: {diag.status.value} -> {diag.primary_failure_mode}")
    print(f"    Confidence: {diag.confidence:.3f} | Epistemic Uncertainty: {diag.epistemic_uncertainty:.3f}")
    print(f"    Evidence: {diag.evidence}")

    # 5. Generate Candidate Actions
    candidates = ActionGenerator.generate_candidates(diag, twin)
    print(f"\n[+] Generated {len(candidates)} candidate recovery actions:")
    for i, c in enumerate(candidates, 1):
        print(f"    {i}. [{c.action_id}] {c.description} (Cost={c.estimated_implementation_cost})")

    # 6. Run Counterfactual Simulation (Simulate 1.2 orbits = 7000s forward on independent clones)
    print("\n[+] Forking Digital Twin state into isolated counterfactual branches...")
    sim = CounterfactualSimulator(default_horizon_sec=7000.0, simulation_step_sec=10.0)
    scenario_results = sim.evaluate_all(twin, candidates)

    # 7. Print Comparative Decision Table
    print("\n" + "=" * 95)
    print(f"{'Action ID':<25} | {'Max Temp':<9} | {'Min Volt':<9} | {'Min SoC':<8} | {'Surv':<5} | {'Payload':<7} | {'Violations'}")
    print("=" * 95)

    records = []
    for res in scenario_results:
        act = res.action
        risk = res.risk_metrics
        imp = res.mission_impact
        viols = len(res.constraint_violations)
        print(f"{act.action_id:<25} | {risk.max_battery_temp_c:>6.1f}°C | {risk.min_bus_voltage_v:>6.1f}V | {risk.min_state_of_charge*100:>5.1f}%  | {str(res.survived):<5} | {imp.payload_availability_fraction*100:>5.0f}%  | {viols} viols")
        
        records.append({
            "action_id": act.action_id,
            "action_type": act.action_type.value,
            "description": act.description,
            "max_temp_c": risk.max_battery_temp_c,
            "min_voltage_v": risk.min_bus_voltage_v,
            "min_soc": risk.min_state_of_charge,
            "joule_heat_kj": risk.cumulative_joule_heat_kj,
            "survived": res.survived,
            "payload_avail_pct": imp.payload_availability_fraction * 100.0,
            "constraint_violations": res.constraint_violations
        })

    # Save results
    out_json = Path("evaluation/05_counterfactual_results.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    print(f"\n[✓] Results saved to: {out_json}")

    # 8. Multi-Branch Trajectory Visualizer
    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)

    # Re-run sample trajectories for plotting
    colors = ["#d62728", "#1f77b4", "#2ca02c", "#9467bd", "#ff7f0e"]
    for idx, act in enumerate(candidates):
        cloned = twin.clone()
        act.apply_to_digital_twin(cloned)
        
        t_arr, temp_arr, soc_arr, volt_arr = [], [], [], []
        for _ in range(700):
            fr = cloned.step(dt_sec=10.0)
            t_arr.append((fr.timestamp - twin.current_time_sec) / 60.0)  # Elapsed minutes
            temp_arr.append(fr.temperature_c)
            soc_arr.append(fr.state_of_charge * 100.0)
            volt_arr.append(fr.voltage_v)

        col = colors[idx % len(colors)]
        label = f"{act.action_id}: {act.action_type.value}"

        axes[0].plot(t_arr, temp_arr, label=label, color=col, lw=1.6)
        axes[1].plot(t_arr, volt_arr, label=label, color=col, lw=1.6)
        axes[2].plot(t_arr, soc_arr, label=label, color=col, lw=1.6)

    axes[0].axhline(48.0, color="red", linestyle="--", alpha=0.7, label="Critical Temp Limit (48°C)")
    axes[0].set_ylabel("Battery Temp [°C]", fontweight="bold")
    axes[0].legend(loc="upper left", fontsize=8, frameon=True)
    axes[0].grid(True, linestyle=":", alpha=0.5)

    axes[1].axhline(22.0, color="red", linestyle="--", alpha=0.7, label="Min Bus Voltage (22V)")
    axes[1].set_ylabel("Bus Voltage [V]", fontweight="bold")
    axes[1].grid(True, linestyle=":", alpha=0.5)

    axes[2].set_ylabel("Battery SoC [%]", fontweight="bold")
    axes[2].set_xlabel("Counterfactual Lookahead Time [Minutes]", fontweight="bold")
    axes[2].grid(True, linestyle=":", alpha=0.5)

    fig.suptitle("AstraHeal Stage 7: Counterfactual Branch Trajectories Under Battery Impedance Fault", fontsize=13, fontweight="bold")
    plt.tight_layout()
    plot_path = Path("docs/figures/05_counterfactual_branches.png")
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[✓] Saved trajectory plot to: {plot_path}")

    print("\n[✓] Stage 7 Counterfactual Simulation Experiment Completed.")


if __name__ == "__main__":
    run_experiment()
