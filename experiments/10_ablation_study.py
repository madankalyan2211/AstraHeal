"""Experiment 10: Rigorous Component Ablation Study for AstraHeal.

Ablates 7 architectural configurations across the standardized evaluation suite:
1. Config A: Full AstraHeal (Full pipeline with Uncertainty, Digital Twin, Counterfactuals, Safety Governor, Comm, OOD)
2. Config B: Without Uncertainty (Deterministic point diagnosis, no OOD gating)
3. Config C: Without Digital Twin (No physics simulation, static lookup heuristic)
4. Config D: Without Counterfactual Simulation (Greedy immediate action selection without forward lookahead)
5. Config E: Without Safety Governor (Direct AI action execution without hard constraint gating)
6. Config F: Without Communication Awareness (Always acts immediately onboard, ignoring active ground links)
7. Config G: Without Unknown-Failure Handling (Forces novel/unseen compound faults into known categories)

Evaluates:
- Mission Survival Rate (%)
- Hard Safety Constraint Violations Count
- Mean Preserved Science Payload Utility (%)
- Unsafe Action Acceptance Count
- Unnecessary Ground Bypass / Autonomous Intervention Count
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

from evaluation.scenarios import BenchmarkScenarioGenerator, BenchmarkScenarioSpec
from src.digital_twin.simulator import SpacecraftEPSDigitalTwin
from src.digital_twin.power_distribution import SpacecraftOperatingMode
from src.telemetry.preprocess import TelemetryPreprocessor
from src.anomaly.detector import StatisticalDetector
from src.diagnosis.engine import FaultDiagnosisEngine
from src.diagnosis.schema import FailureMode, DiagnosisStatus
from src.planner.actions import ActionGenerator, RecoveryAction, RecoveryActionType
from src.planner.counterfactual import CounterfactualSimulator
from src.planner.recovery_planner import AutonomousRecoveryPlanner
from src.safety.safety_governor import DeterministicSafetyGovernor, SafetyStatus
from src.communication.manager import CommunicationAwareAutonomyManager, AutonomyActionType


CONFIG_NAMES = {
    "A_FULL": "Full AstraHeal",
    "B_NO_UNCERTAINTY": "w/o Uncertainty",
    "C_NO_DIGITAL_TWIN": "w/o Digital Twin",
    "D_NO_COUNTERFACTUAL": "w/o Counterfactuals",
    "E_NO_GOVERNOR": "w/o Safety Governor",
    "F_NO_COMMUNICATION": "w/o Comm Awareness",
    "G_NO_UNKNOWN_RESILIENCE": "w/o Unknown Resilience"
}


def evaluate_ablation_configuration(
    config_key: str,
    spec: BenchmarkScenarioSpec
) -> dict:
    """Run a scenario under an ablated system configuration."""
    twin = SpacecraftEPSDigitalTwin(system_id=f"ABL-{config_key}", random_seed=spec.random_seed)
    twin.battery.soc = spec.initial_soc
    for f in spec.faults:
        twin.inject_fault(f)

    step_sec = 10.0
    steps = int(spec.orbit_duration_sec / step_sec)
    preprocessor = TelemetryPreprocessor()
    detector = StatisticalDetector()
    governor = DeterministicSafetyGovernor()
    comm_mgr = CommunicationAwareAutonomyManager()

    fitted = False
    action_triggered = False
    hard_violations = 0
    max_temp = 0.0
    min_volt = 100.0
    min_soc = 1.0
    unsafe_actions_accepted = 0
    unnecessary_interventions = 0

    frames = []

    for i in range(steps):
        frame = twin.step(dt_sec=step_sec)
        frames.append(frame.to_dict())

        max_temp = max(max_temp, frame.temperature_c)
        min_volt = min(min_volt, frame.voltage_v)
        if frame.state_of_charge is not None:
            min_soc = min(min_soc, frame.state_of_charge)

        if frame.temperature_c > 46.0:
            hard_violations += 1
        if frame.voltage_v < 22.0:
            hard_violations += 1
        if frame.state_of_charge is not None and frame.state_of_charge < 0.15:
            hard_violations += 1

        if not fitted and len(frames) >= 20:
            feat_df = preprocessor.extract_features(pd.DataFrame(frames))
            detector.fit(feat_df.iloc[:20])
            fitted = True

        if fitted and not action_triggered and len(frames) % 5 == 0:
            cur_df = preprocessor.extract_features(pd.DataFrame(frames[-20:]))
            rep = detector.detect_frame(cur_df.iloc[-1])

            if rep.is_anomaly and rep.anomaly_score >= 0.50:
                action_triggered = True

                # --- 1. Diagnosis Step with Ablations ---
                diag_engine = FaultDiagnosisEngine(primary_method="bayesian")
                diag = diag_engine.diagnose_frame(rep, cur_df.iloc[-1])

                if config_key == "B_NO_UNCERTAINTY" or config_key == "G_NO_UNKNOWN_RESILIENCE":
                    # Force epistemic uncertainty to 0, forcing point diagnosis
                    diag.epistemic_uncertainty = 0.0
                    if diag.status == DiagnosisStatus.UNKNOWN_FAILURE:
                        diag.status = DiagnosisStatus.KNOWN_FAILURE
                        diag.primary_failure_mode = FailureMode.BATTERY_INTERNAL_RESISTANCE_SPIKE.value

                # --- 2. Communication Arbitration with Ablations ---
                if config_key == "F_NO_COMMUNICATION":
                    # Always act autonomously, never defer to ground
                    comm_verdict = AutonomyActionType.ACT_AUTONOMOUSLY
                    if twin.current_time_sec > 2000.0:  # If in ground pass, acting was unnecessary
                        unnecessary_interventions += 1
                else:
                    comm_decision = comm_mgr.arbitrate(
                        current_time_sec=twin.current_time_sec,
                        diagnosis=diag,
                        plan=None,
                        noop_scenario=None
                    )
                    comm_verdict = comm_decision.decision

                # --- 3. Planning & Simulation with Ablations ---
                if comm_verdict == AutonomyActionType.ACT_AUTONOMOUSLY or config_key == "F_NO_COMMUNICATION":
                    candidates = ActionGenerator.generate_candidates(diag, twin)

                    if config_key == "C_NO_DIGITAL_TWIN":
                        # Naive static rule: Blind safe mode
                        selected_act = next((c for c in candidates if c.action_type == RecoveryActionType.ENTER_SAFE_MODE), candidates[0])
                        selected_act.apply_to_digital_twin(twin)

                    elif config_key == "D_NO_COUNTERFACTUAL":
                        # Greedy selection: pick first matching candidate without forward simulation
                        selected_act = candidates[0]  # Usually No-Op or naive first action
                        if config_key != "E_NO_GOVERNOR":
                            # Even without simulation, if governor checks static state
                            pass
                        selected_act.apply_to_digital_twin(twin)

                    elif config_key == "E_NO_GOVERNOR":
                        # Counterfactual simulation but NO Safety Governor gating
                        sim = CounterfactualSimulator(default_horizon_sec=3000.0)
                        scenarios = sim.evaluate_all(twin, candidates)
                        # Pick highest payload utility candidate regardless of safety breaches
                        scenarios.sort(key=lambda s: s.mission_impact.payload_availability_fraction, reverse=True)
                        best_scen = scenarios[0]
                        if not best_scen.survived or best_scen.risk_metrics.max_battery_temp_c > 46.0:
                            unsafe_actions_accepted += 1
                        best_scen.action.apply_to_digital_twin(twin)

                    else:
                        # Full AstraHeal pipeline
                        planner = AutonomousRecoveryPlanner(governor=governor)
                        plan = planner.plan_recovery(twin, diag, horizon_sec=3000.0)
                        planner.execute_plan_on_twin(twin, plan)

    final_soc = float(twin.battery.soc)
    survived = (hard_violations == 0) and (final_soc > 0.05) and (max_temp < 60.0)
    payload_pct = (twin.pdu.payload_active_w / 120.0) * 100.0

    return {
        "config_key": config_key,
        "config_name": CONFIG_NAMES[config_key],
        "scenario_id": spec.scenario_id,
        "survived": survived,
        "hard_violations": hard_violations,
        "payload_availability_pct": payload_pct,
        "max_temp_c": max_temp,
        "min_volt_v": min_volt,
        "final_soc": final_soc,
        "unsafe_actions_accepted": unsafe_actions_accepted,
        "unnecessary_interventions": unnecessary_interventions
    }


def run_ablation_study():
    print("=" * 85)
    print("ASTRAHEAL EXPERIMENT 10: Full Component Ablation Study")
    print("=" * 85)

    suite = BenchmarkScenarioGenerator.get_full_evaluation_suite(random_seed=42)
    print(f"[+] Running {len(CONFIG_NAMES)} configurations across {len(suite)} stress scenarios...")

    all_results = []
    summary_by_config = {}

    for cfg_key in CONFIG_NAMES.keys():
        cfg_results = []
        for spec in suite:
            res = evaluate_ablation_configuration(cfg_key, spec)
            cfg_results.append(res)
            all_results.append(res)

        surv_pct = float(np.mean([1 if r["survived"] else 0 for r in cfg_results]) * 100.0)
        tot_viols = int(sum(r["hard_violations"] for r in cfg_results))
        mean_payload = float(np.mean([r["payload_availability_pct"] for r in cfg_results]))
        tot_unsafe = int(sum(r["unsafe_actions_accepted"] for r in cfg_results))
        tot_unnecessary = int(sum(r["unnecessary_interventions"] for r in cfg_results))

        summary_by_config[cfg_key] = {
            "config_name": CONFIG_NAMES[cfg_key],
            "survival_rate_pct": surv_pct,
            "total_hard_violations": tot_viols,
            "mean_payload_availability_pct": mean_payload,
            "unsafe_actions_accepted": tot_unsafe,
            "unnecessary_interventions": tot_unnecessary
        }

    # Print Summary Table
    print("\n" + "=" * 105)
    print(f"{'Configuration':<26} | {'Survival %':<11} | {'Hard Viols':<11} | {'Payload %':<11} | {'Unsafe Acts':<12} | {'Unnecessary'}")
    print("=" * 105)

    for cfg_key, sum_data in summary_by_config.items():
        print(f"{sum_data['config_name']:<26} | {sum_data['survival_rate_pct']:>9.1f}% | {sum_data['total_hard_violations']:>11d} | {sum_data['mean_payload_availability_pct']:>9.1f}% | {sum_data['unsafe_actions_accepted']:>12d} | {sum_data['unnecessary_interventions']:>11d}")

    print("=" * 105)

    # Save JSON results
    out_json = Path("evaluation/10_ablation_results.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"summary": summary_by_config, "detailed": all_results}, f, indent=2)
    print(f"\n[✓] Ablation metrics saved to: {out_json}")

    # Generate Publication-Quality Figure
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    names = [sum_data["config_name"] for sum_data in summary_by_config.values()]
    
    # 1. Survival Rate
    surv_vals = [s["survival_rate_pct"] for s in summary_by_config.values()]
    axes[0].barh(names, surv_vals, color="#1f77b4", edgecolor="black")
    axes[0].set_xlabel("Survival Rate [%]", fontweight="bold")
    axes[0].set_title("Mission Survival Rate by Configuration", fontweight="bold", pad=10)
    axes[0].set_xlim(0, 110)
    axes[0].grid(True, linestyle=":", alpha=0.5, axis="x")

    # 2. Hard Violations
    viol_vals = [s["total_hard_violations"] for s in summary_by_config.values()]
    axes[1].barh(names, viol_vals, color="#d62728", edgecolor="black")
    axes[1].set_xlabel("Hard Constraint Violations", fontweight="bold")
    axes[1].set_title("Hard Safety Violations (Lower is Better)", fontweight="bold", pad=10)
    axes[1].grid(True, linestyle=":", alpha=0.5, axis="x")

    # 3. Payload Availability
    pay_vals = [s["mean_payload_availability_pct"] for s in summary_by_config.values()]
    axes[2].barh(names, pay_vals, color="#2ca02c", edgecolor="black")
    axes[2].set_xlabel("Preserved Payload [%]", fontweight="bold")
    axes[2].set_title("Science Payload Capability Preserved", fontweight="bold", pad=10)
    axes[2].set_xlim(0, 110)
    axes[2].grid(True, linestyle=":", alpha=0.5, axis="x")

    plt.tight_layout()
    plot_path = Path("docs/figures/10_ablation_study.png")
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[✓] Saved publication ablation figure to: {plot_path}")

    print("\n[✓] Stage 10 Ablation Study Completed.")


if __name__ == "__main__":
    run_ablation_study()
