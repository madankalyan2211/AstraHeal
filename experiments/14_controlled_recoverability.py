"""Experiment 14: Controlled Recoverability Benchmark & Multi-System Decision Value Study.

Investigates:
"Does uncertainty-aware counterfactual planning produce better mission-utility decisions
than passive operation or blind Safe Mode when a fault is physically recoverable?"

Evaluates 8 deterministic controlled scenarios where software intervention CAN materially change the outcome:
1. SC-01-RECOV-ECLIPSE-SURGE: Moderate battery impedance surge (4.0x) in eclipse -> NOOP causes undervoltage, Throttle 50% preserves bus & 50% payload.
2. SC-02-RECOV-PAYLOAD-OVERLOAD: Payload parasitic draw (180W) -> NOOP depletes battery, Throttling stabilizes bus.
3. SC-03-RECOV-MODERATE-THERMAL: 55W exothermic heat (below 65W radiator capacity) -> Throttling/Safe Mode caps temp below 46°C.
4. SC-04-RECOV-COMPOUND-ECLIPSE: Battery degradation + science payload in eclipse -> Throttling keeps SoC above 15% floor.
5. SC-05-COMM-BLACKOUT-CRITICAL: Urgent fault during 40-min ground blackout -> ACT_AUTONOMOUSLY prevents failure.
6. SC-06-COMM-PASS-BENIGN: Non-critical drift during active Svalbard pass -> WAIT_FOR_GROUND defers safely to operators.
7. SC-07-OOD-COMPOUND-ABSTAIN: Novel compound fault (u_ep > 0.85) -> Correct abstention from aggressive action; safe standby.
8. SC-08-BENIGN-LOAD-PULSE: Transient science mode step pulse -> AstraHeal chooses NOOP without false safe mode entry.

Compares:
- BASELINE A: Passive / No Recovery
- BASELINE B: Blind Safe Mode (immediate shutdown)
- ASTRAHEAL: Detection -> Evidential Diagnosis -> Uncertainty -> Counterfactual Lookahead -> Safety Governor -> Utility Selection
- ABLATIONS: w/o Uncertainty, w/o Counterfactuals, w/o Safety Governor, w/o Comm Awareness
"""

import sys
import json
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from src.digital_twin.simulator import SpacecraftEPSDigitalTwin
from src.digital_twin.fault_injection import InjectedFaultSpec, FaultType
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


# Fixed, Documented Objective Mission Utility Weights
W_SURVIVAL = 0.45
W_PAYLOAD = 0.30
W_ENERGY = 0.15
W_VIOLATION = 0.10


class ControlledScenarioSpec(BaseModel):
    """Specification of a controlled recoverable scenario."""
    scenario_id: str
    name: str
    category: str
    orbit_duration_sec: float = 11480.0  # 2 full orbits
    initial_soc: float = 0.95
    faults: List[InjectedFaultSpec] = Field(default_factory=list)
    is_physically_recoverable: bool = True
    expected_optimal_action: str
    description: str


class ControlledExecutionResult(BaseModel):
    """Detailed result for a single scenario execution."""
    system_name: str
    scenario_id: str
    scenario_name: str
    survived: bool
    recovery_successful: bool
    payload_retention_pct: float
    delivered_payload_wh: float
    energy_retention_wh: float
    final_soc_pct: float
    min_bus_voltage_v: float
    max_battery_temp_c: float
    thermal_margin_c: float
    voltage_margin_v: float
    hard_violations_count: int
    executed_unsafe_actions: int
    governor_bypasses: int
    governor_rejections: int
    unnecessary_interventions: int
    selected_action_id: Optional[str]
    selected_action_type: Optional[str]
    diagnosis_status: str
    primary_failure_mode: str
    epistemic_uncertainty: float
    aleatoric_uncertainty: float
    comm_decision: str
    mission_utility_score: float
    predicted_vs_actual_temp_error_c: float
    predicted_vs_actual_volt_error_v: float


def get_controlled_scenarios() -> List[ControlledScenarioSpec]:
    """Define the 8 standardized controlled recoverable scenarios."""
    return [
        ControlledScenarioSpec(
            scenario_id="SC-01-ECLIPSE-SURGE",
            name="Moderate Battery Impedance Surge in Eclipse",
            category="RECOVERABLE_BATTERY",
            orbit_duration_sec=11480.0,
            initial_soc=0.95,
            faults=[
                InjectedFaultSpec(fault_type=FaultType.BATTERY_RESISTANCE_SPIKE, start_time_sec=600.0, parameters={"resistance_multiplier": 3.8})
            ],
            is_physically_recoverable=True,
            expected_optimal_action="ACT-02-THROTTLE-PAYLOAD-50",
            description="In eclipse, high impedance causes voltage sag and Joule heat. Throttling payload 50% keeps bus stable & maintains science."
        ),
        ControlledScenarioSpec(
            scenario_id="SC-02-PAYLOAD-OVERLOAD",
            name="Recoverable Science Payload Overload (180W draw)",
            category="RECOVERABLE_POWER",
            orbit_duration_sec=11480.0,
            initial_soc=0.95,
            faults=[
                InjectedFaultSpec(fault_type=FaultType.PARASITIC_LOAD_SURGE, start_time_sec=1000.0, parameters={"extra_load_w": 180.0})
            ],
            is_physically_recoverable=True,
            expected_optimal_action="ACT-03-DISABLE-PAYLOAD",
            description="Parasitic short in payload electronics. Shedding payload preserves bus voltage above 22V lockout."
        ),
        ControlledScenarioSpec(
            scenario_id="SC-03-MODERATE-THERMAL",
            name="Moderate Thermal Runaway (55W Heat, below 65W Radiator)",
            category="RECOVERABLE_THERMAL",
            orbit_duration_sec=11480.0,
            initial_soc=0.95,
            faults=[
                InjectedFaultSpec(fault_type=FaultType.THERMAL_RUNAWAY, start_time_sec=3000.0, parameters={"exothermic_heat_w": 55.0})
            ],
            is_physically_recoverable=True,
            expected_optimal_action="ACT-01-SAFE-MODE",
            description="Exothermic reaction at 55W is within radiator rejection capacity (65W). Load shedding caps temperature at 43.5°C."
        ),
        ControlledScenarioSpec(
            scenario_id="SC-04-COMPOUND-ECLIPSE",
            name="Battery Degradation with High Science Load in Eclipse",
            category="RECOVERABLE_BATTERY",
            orbit_duration_sec=11480.0,
            initial_soc=0.70,
            faults=[
                InjectedFaultSpec(fault_type=FaultType.BATTERY_RESISTANCE_SPIKE, start_time_sec=400.0, parameters={"resistance_multiplier": 3.0})
            ],
            is_physically_recoverable=True,
            expected_optimal_action="ACT-02-THROTTLE-PAYLOAD-50",
            description="Lower initial SoC in shadow with impedance spike. Throttling prevents breaching 15% reserve floor."
        ),
        ControlledScenarioSpec(
            scenario_id="SC-05-BLACKOUT-CRITICAL",
            name="Urgent Impedance Surge in Ground Blackout Occultation",
            category="COMMUNICATION_BLACKOUT",
            orbit_duration_sec=11480.0,
            initial_soc=0.95,
            faults=[
                InjectedFaultSpec(fault_type=FaultType.BATTERY_RESISTANCE_SPIKE, start_time_sec=800.0, parameters={"resistance_multiplier": 4.2})
            ],
            is_physically_recoverable=True,
            expected_optimal_action="ACT-02-THROTTLE-PAYLOAD-50",
            description="Fault in deep communication blackout (next pass in 40 mins). Onboard autonomous action is mandatory."
        ),
        ControlledScenarioSpec(
            scenario_id="SC-06-PASS-BENIGN",
            name="Non-Critical Sensor Bias During Active Ground Pass",
            category="COMMUNICATION_PASS",
            orbit_duration_sec=11480.0,
            initial_soc=0.95,
            faults=[
                InjectedFaultSpec(fault_type=FaultType.SENSOR_BIAS_DRIFT, start_time_sec=2400.0, parameters={"bias_offset": -2.5, "channel": "voltage_v"})
            ],
            is_physically_recoverable=True,
            expected_optimal_action="WAIT_FOR_GROUND",
            description="Direct link with Svalbard station active. System defers to ground operators without unnecessary onboard disruption."
        ),
        ControlledScenarioSpec(
            scenario_id="SC-07-OOD-COMPOUND-ABSTAIN",
            name="Novel Out-Of-Distribution Compound Anomaly",
            category="UNKNOWN_OOD",
            orbit_duration_sec=11480.0,
            initial_soc=0.95,
            faults=[
                InjectedFaultSpec(fault_type=FaultType.SOLAR_STRING_FAULT, start_time_sec=1500.0, parameters={"remaining_health": 0.35}),
                InjectedFaultSpec(fault_type=FaultType.PARASITIC_LOAD_SURGE, start_time_sec=2000.0, parameters={"extra_load_w": 120.0})
            ],
            is_physically_recoverable=True,
            expected_optimal_action="ACT-04-CONSERVATIVE-STANDBY",
            description="Unseen concurrent failure mode (u_epistemic > 0.85). Correctly inhibits aggressive single-fault actions; safe standby."
        ),
        ControlledScenarioSpec(
            scenario_id="SC-08-BENIGN-LOAD-PULSE",
            name="Transient Science Instrument Calibration Pulse",
            category="BENIGN_TRANSIENT",
            orbit_duration_sec=11480.0,
            initial_soc=0.95,
            faults=[],  # Nominal instrument operation with natural load variations
            is_physically_recoverable=True,
            expected_optimal_action="ACT-00-NOOP",
            description="Nominal mission with mode step transients. Tests that AstraHeal selects NOOP without spurious Safe Mode triggering."
        )
    ]


def execute_controlled_scenario(
    system_type: str,
    spec: ControlledScenarioSpec
) -> ControlledExecutionResult:
    """Execute a single scenario under a specified architecture configuration."""
    twin = SpacecraftEPSDigitalTwin(system_id=f"CTRL-{system_type}", random_seed=42)
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
    action_executed = False
    
    frames = []
    hard_violations = 0
    max_temp = 0.0
    min_volt = 100.0
    min_soc = 1.0
    cumulative_payload_wh = 0.0

    selected_act_id = None
    selected_act_type = None
    diag_status = "NOMINAL"
    diag_mode = "NOMINAL_OPERATION"
    u_epistemic = 0.0
    u_aleatoric = 0.0
    comm_decision_str = "N/A"
    gov_rejections = 0
    unsafe_actions = 0
    gov_bypasses = 0
    unnecessary_interventions = 0
    
    predicted_max_temp = None
    predicted_min_volt = None

    for step_idx in range(steps):
        current_t = twin.current_time_sec
        frame = twin.step(dt_sec=step_sec)
        frames.append(frame.to_dict())

        max_temp = max(max_temp, frame.temperature_c)
        min_volt = min(min_volt, frame.voltage_v)
        if frame.state_of_charge is not None:
            min_soc = min(min_soc, frame.state_of_charge)

        # Accumulate payload delivered
        payload_w = twin.pdu.payload_active_w
        cumulative_payload_wh += (payload_w * step_sec) / 3600.0

        # Physical hard limit checking
        if frame.temperature_c > 46.0 or frame.voltage_v < 22.0 or (frame.state_of_charge is not None and frame.state_of_charge < 0.15):
            hard_violations += 1

        # Fit detector on early nominal frames
        if not fitted and len(frames) >= 30:
            feat_df = preprocessor.extract_features(pd.DataFrame(frames))
            detector.fit(feat_df.iloc[:30])
            fitted = True

        # Anomaly detection & single-intervention evaluation at fault onset
        if fitted and not action_executed and len(frames) % 5 == 0 and len(frames) >= 35:
            cur_df = preprocessor.extract_features(pd.DataFrame(frames[-25:]))
            rep = detector.detect_frame(cur_df.iloc[-1])

            if rep.is_anomaly and rep.anomaly_score >= 0.50:
                action_executed = True

                # 1. Evidential Bayesian Diagnosis
                diag_engine = FaultDiagnosisEngine(primary_method="bayesian")
                diag = diag_engine.diagnose_frame(rep, cur_df.iloc[-1])
                diag_status = diag.status.value
                diag_mode = diag.primary_failure_mode
                u_epistemic = float(diag.epistemic_uncertainty)
                u_aleatoric = float(diag.aleatoric_uncertainty)

                # Ablation: Without Uncertainty
                if system_type == "ABL_NO_UNCERTAINTY":
                    diag.epistemic_uncertainty = 0.0
                    u_epistemic = 0.0

                # Forward lookahead simulation for candidate actions
                candidates = ActionGenerator.generate_candidates(diag, twin)
                sim = CounterfactualSimulator(default_horizon_sec=3000.0)
                scenarios = sim.evaluate_all(twin, candidates)
                noop_scen = next((s for s in scenarios if s.action.action_type == RecoveryActionType.CONTINUE_NOMINAL), scenarios[0] if scenarios else None)

                # 2. Communication Arbitration with evaluated no-op urgency
                comm_dec = comm_mgr.arbitrate(current_t, diag, None, noop_scenario=noop_scen)
                comm_decision_str = comm_dec.decision.value

                # Ablation: Without Communication Awareness
                if system_type == "ABL_NO_COMMUNICATION":
                    comm_decision_str = "ACT_AUTONOMOUSLY"
                    comm_dec.decision = AutonomyActionType.ACT_AUTONOMOUSLY
                    if current_t >= 2300.0 and current_t <= 2900.0:
                        unnecessary_interventions += 1

                # 3. Decision & Execution
                if system_type == "BASELINE_A":
                    selected_act_id = "ACT-00-NOOP"
                    selected_act_type = "CONTINUE_NOMINAL"

                elif system_type == "BASELINE_B":
                    selected_act_id = "ACT-01-SAFE-MODE"
                    selected_act_type = "ENTER_SAFE_MODE"
                    twin.pdu.set_mode(SpacecraftOperatingMode.SAFE_MODE)
                    if not spec.faults:
                        unnecessary_interventions += 1

                elif system_type.startswith("ABL_NO_COUNTERFACTUAL"):
                    # Greedy first candidate without forward simulation
                    candidates = ActionGenerator.generate_candidates(diag, twin)
                    selected_act = candidates[0]
                    selected_act_id = selected_act.action_id
                    selected_act_type = selected_act.action_type.value
                    selected_act.apply_to_digital_twin(twin)

                elif system_type == "ABL_NO_SAFETY_GOVERNOR":
                    # Counterfactual simulation but unconstrained AI choice (picks highest payload regardless of safety)
                    candidates = ActionGenerator.generate_candidates(diag, twin)
                    sim = CounterfactualSimulator(default_horizon_sec=3000.0)
                    scenarios = sim.evaluate_all(twin, candidates)
                    scenarios.sort(key=lambda s: s.mission_impact.payload_availability_fraction, reverse=True)
                    best_scen = scenarios[0]
                    selected_act_id = best_scen.action.action_id
                    selected_act_type = best_scen.action.action_type.value
                    if not best_scen.survived or best_scen.risk_metrics.max_battery_temp_c > 46.0:
                        unsafe_actions += 1
                    best_scen.action.apply_to_digital_twin(twin)
                    predicted_max_temp = best_scen.risk_metrics.max_battery_temp_c
                    predicted_min_volt = best_scen.risk_metrics.min_bus_voltage_v

                else:
                    # Full AstraHeal (or other ablations with governor active)
                    planner = AutonomousRecoveryPlanner(governor=governor)
                    plan = planner.plan_recovery(twin, diag, horizon_sec=3000.0)
                    gov_rejections = plan.rejected_candidates_count

                    if comm_dec.decision == AutonomyActionType.ACT_AUTONOMOUSLY:
                        if plan.selected_action:
                            selected_act_id = plan.selected_action.action_id
                            selected_act_type = plan.selected_action.action_type.value
                            planner.execute_plan_on_twin(twin, plan)
                            
                            # Capture lookahead predictions for error comparison
                            sel_scen = next((s for s in plan.all_evaluated_scenarios if s["action_id"] == selected_act_id), None)
                            if sel_scen:
                                predicted_max_temp = sel_scen["max_temp_c"]
                                predicted_min_volt = sel_scen["min_voltage_v"]
                    else:
                        selected_act_id = "WAIT_FOR_GROUND"
                        selected_act_type = "DEFERRED_TO_GROUND"

    # Outcome evaluation
    final_soc = float(twin.battery.soc)
    survived = (hard_violations == 0) and (final_soc > 0.10) and (max_temp < 48.0)
    
    max_possible_payload_wh = (120.0 * spec.orbit_duration_sec) / 3600.0
    payload_pct = (cumulative_payload_wh / max_possible_payload_wh) * 100.0
    
    thermal_margin = 46.0 - max_temp
    voltage_margin = min_volt - 22.0
    energy_retention_wh = max(0.0, (final_soc - 0.15) * twin.battery.capacity_actual_ah * 28.0)

    # Mission Utility Score computation (Standardized fixed formula)
    norm_surv = 1.0 if survived else 0.0
    norm_pay = max(0.0, min(1.0, cumulative_payload_wh / max_possible_payload_wh))
    norm_eng = max(0.0, min(1.0, energy_retention_wh / 600.0))
    norm_viol = min(1.0, hard_violations / 100.0)
    
    utility_score = (
        W_SURVIVAL * norm_surv
        + W_PAYLOAD * norm_pay
        + W_ENERGY * norm_eng
        - W_VIOLATION * norm_viol
    )

    # Prediction error
    temp_err = abs(predicted_max_temp - max_temp) if predicted_max_temp is not None else 0.0
    volt_err = abs(predicted_min_volt - min_volt) if predicted_min_volt is not None else 0.0

    recov_success = survived and (hard_violations == 0)

    return ControlledExecutionResult(
        system_name=system_type,
        scenario_id=spec.scenario_id,
        scenario_name=spec.name,
        survived=survived,
        recovery_successful=recov_success,
        payload_retention_pct=float(payload_pct),
        delivered_payload_wh=float(cumulative_payload_wh),
        energy_retention_wh=float(energy_retention_wh),
        final_soc_pct=float(final_soc * 100.0),
        min_bus_voltage_v=float(min_volt),
        max_battery_temp_c=float(max_temp),
        thermal_margin_c=float(thermal_margin),
        voltage_margin_v=float(voltage_margin),
        hard_violations_count=int(hard_violations),
        executed_unsafe_actions=int(unsafe_actions),
        governor_bypasses=int(gov_bypasses),
        governor_rejections=int(gov_rejections),
        unnecessary_interventions=int(unnecessary_interventions),
        selected_action_id=selected_act_id,
        selected_action_type=selected_act_type,
        diagnosis_status=diag_status,
        primary_failure_mode=diag_mode,
        epistemic_uncertainty=float(u_epistemic),
        aleatoric_uncertainty=float(u_aleatoric),
        comm_decision=comm_decision_str,
        mission_utility_score=float(utility_score),
        predicted_vs_actual_temp_error_c=float(temp_err),
        predicted_vs_actual_volt_error_v=float(volt_err)
    )


def run_controlled_experiment():
    print("=" * 85)
    print("ASTRAHEAL EXPERIMENT 14: Controlled Recoverability Benchmark & Decision Study")
    print("=" * 85)

    scenarios = get_controlled_scenarios()
    print(f"[+] Loaded {len(scenarios)} controlled recoverable scenarios.")

    systems = [
        "BASELINE_A",
        "BASELINE_B",
        "ASTRAHEAL",
        "ABL_NO_UNCERTAINTY",
        "ABL_NO_COUNTERFACTUAL",
        "ABL_NO_SAFETY_GOVERNOR",
        "ABL_NO_COMMUNICATION"
    ]

    results_by_sys: Dict[str, List[ControlledExecutionResult]] = {s: [] for s in systems}

    for sc in scenarios:
        print(f"\n[Evaluating Scenario: {sc.scenario_id}] {sc.name}")
        for sys_name in systems:
            res = execute_controlled_scenario(sys_name, sc)
            results_by_sys[sys_name].append(res)
            if sys_name in ["BASELINE_A", "BASELINE_B", "ASTRAHEAL"]:
                surv_str = "SURVIVED" if res.survived else "FAILED"
                print(f"  • {sys_name:<12} -> {surv_str} | Utility: {res.mission_utility_score:.3f} | Payload: {res.payload_retention_pct:.1f}% ({res.delivered_payload_wh:.1f}Wh) | Viols: {res.hard_violations_count} | Action: {res.selected_action_id}")

    # Compute Summary Statistics
    summary_table = {}
    for sys_name, res_list in results_by_sys.items():
        n = len(res_list)
        surv_pct = float(np.mean([1 if r.survived else 0 for r in res_list]) * 100.0)
        mean_util = float(np.mean([r.mission_utility_score for r in res_list]))
        mean_pay_pct = float(np.mean([r.payload_retention_pct for r in res_list]))
        mean_pay_wh = float(np.mean([r.delivered_payload_wh for r in res_list]))
        tot_viols = int(sum(r.hard_violations_count for r in res_list))
        tot_unsafe = int(sum(r.executed_unsafe_actions for r in res_list))
        tot_gov_rejects = int(sum(r.governor_rejections for r in res_list))
        mean_t_err = float(np.mean([r.predicted_vs_actual_temp_error_c for r in res_list]))
        mean_v_err = float(np.mean([r.predicted_vs_actual_volt_error_v for r in res_list]))

        summary_table[sys_name] = {
            "survival_pct": surv_pct,
            "mean_mission_utility": mean_util,
            "mean_payload_retention_pct": mean_pay_pct,
            "mean_delivered_payload_wh": mean_pay_wh,
            "total_hard_violations": tot_viols,
            "executed_unsafe_actions": tot_unsafe,
            "total_governor_rejections": tot_gov_rejects,
            "mean_temp_prediction_error_c": mean_t_err,
            "mean_volt_prediction_error_v": mean_v_err
        }

    # Print Master Summary Table
    print("\n" + "=" * 115)
    print(f"{'System Architecture':<24} | {'Survival %':<11} | {'Utility Score':<14} | {'Payload %':<11} | {'Payload Wh':<12} | {'Violations':<11} | {'Unsafe Acts'}")
    print("=" * 115)

    for sys_name, s in summary_table.items():
        print(f"{sys_name:<24} | {s['survival_pct']:>9.1f}% | {s['mean_mission_utility']:>12.3f}   | {s['mean_payload_retention_pct']:>9.1f}% | {s['mean_delivered_payload_wh']:>10.1f}Wh | {s['total_hard_violations']:>11d} | {s['executed_unsafe_actions']:>11d}")

    print("=" * 115)

    # Save JSON Output
    out_json = Path("evaluation/14_controlled_results.json")
    out_json.parent.mkdir(parents=True, exist_ok=True)
    serialized = {
        "summary": summary_table,
        "scenarios": {k: [r.model_dump() for r in v] for k, v in results_by_sys.items()}
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(serialized, f, indent=2)
    print(f"\n[✓] Controlled benchmark results saved to: {out_json}")

    # Generate Publication Figures (8 Figures under docs/figures/14_controlled_recoverability/)
    fig_dir = Path("docs/figures/14_controlled_recoverability")
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Figure 1: Mission Utility Score Comparison
    fig1, ax1 = plt.subplots(figsize=(9, 5))
    sys_labels = ["Baseline A\n(Passive)", "Baseline B\n(Blind Safe)", "AstraHeal\n(Autonomous)", "w/o Unc", "w/o CF", "w/o Gov", "w/o Comm"]
    util_scores = [summary_table[k]["mean_mission_utility"] for k in systems]
    colors = ["#d62728", "#ff7f0e", "#2ca02c", "#1f77b4", "#9467bd", "#8c564b", "#e377c2"]
    bars1 = ax1.bar(sys_labels, util_scores, color=colors, edgecolor="black", width=0.55)
    ax1.set_ylabel("Standardized Mission Utility Score", fontweight="bold")
    ax1.set_title("Figure 1: Mission Utility Score Across Controlled Architectures", fontweight="bold", pad=12)
    ax1.grid(True, linestyle=":", alpha=0.5, axis="y")
    for b in bars1:
        y = b.get_height()
        ax1.text(b.get_x() + b.get_width()/2.0, y + 0.01, f"{y:.3f}", ha="center", va="bottom", fontweight="bold", fontsize=8)
    plt.tight_layout()
    plt.savefig(fig_dir / "01_mission_utility_comparison.png", dpi=200)
    plt.close(fig1)

    # Figure 2: Payload Retention (Wh) Comparison
    fig2, ax2 = plt.subplots(figsize=(9, 5))
    pay_whs = [summary_table[k]["mean_delivered_payload_wh"] for k in systems]
    bars2 = ax2.bar(sys_labels, pay_whs, color=colors, edgecolor="black", width=0.55)
    ax2.set_ylabel("Delivered Payload Energy [Wh]", fontweight="bold")
    ax2.set_title("Figure 2: Science Payload Energy Delivered Across Configurations", fontweight="bold", pad=12)
    ax2.grid(True, linestyle=":", alpha=0.5, axis="y")
    for b in bars2:
        y = b.get_height()
        ax2.text(b.get_x() + b.get_width()/2.0, y + 5, f"{y:.1f}Wh", ha="center", va="bottom", fontweight="bold", fontsize=8)
    plt.tight_layout()
    plt.savefig(fig_dir / "02_payload_retention_comparison.png", dpi=200)
    plt.close(fig2)

    # Figure 3: Survival Rate Comparison
    fig3, ax3 = plt.subplots(figsize=(9, 5))
    surv_rates = [summary_table[k]["survival_pct"] for k in systems]
    bars3 = ax3.bar(sys_labels, surv_rates, color=colors, edgecolor="black", width=0.55)
    ax3.set_ylabel("Mission Survival Rate [%]", fontweight="bold")
    ax3.set_ylim(0, 115)
    ax3.set_title("Figure 3: Mission Survival Rate Across Recoverable Scenarios", fontweight="bold", pad=12)
    ax3.grid(True, linestyle=":", alpha=0.5, axis="y")
    for b in bars3:
        y = b.get_height()
        ax3.text(b.get_x() + b.get_width()/2.0, y + 2, f"{y:.1f}%", ha="center", va="bottom", fontweight="bold", fontsize=8)
    plt.tight_layout()
    plt.savefig(fig_dir / "03_recovery_success_comparison.png", dpi=200)
    plt.close(fig3)

    # Figure 4: Counterfactual Predicted vs Actual Error
    fig4, ax4 = plt.subplots(figsize=(8, 5))
    scen_ids = [sc.scenario_id for sc in scenarios]
    t_errs = [r.predicted_vs_actual_temp_error_c for r in results_by_sys["ASTRAHEAL"]]
    v_errs = [r.predicted_vs_actual_volt_error_v for r in results_by_sys["ASTRAHEAL"]]
    x_idx = np.arange(len(scen_ids))
    width = 0.35
    ax4.bar(x_idx - width/2, t_errs, width, label="Temperature Error (|Pred - Actual| °C)", color="#ef4444")
    ax4.bar(x_idx + width/2, v_errs, width, label="Voltage Error (|Pred - Actual| V)", color="#06b6d4")
    ax4.set_xticks(x_idx)
    ax4.set_xticklabels(scen_ids, rotation=25, ha="right", fontsize=8)
    ax4.set_ylabel("Absolute Prediction Error", fontweight="bold")
    ax4.set_title("Figure 4: Counterfactual Lookahead Digital Twin Prediction Error", fontweight="bold", pad=12)
    ax4.legend()
    ax4.grid(True, linestyle=":", alpha=0.5, axis="y")
    plt.tight_layout()
    plt.savefig(fig_dir / "04_counterfactual_prediction_error.png", dpi=200)
    plt.close(fig4)

    # Figure 5: Uncertainty vs Abstention
    fig5, ax5 = plt.subplots(figsize=(8, 5))
    ep_uncs = [r.epistemic_uncertainty for r in results_by_sys["ASTRAHEAL"]]
    al_uncs = [r.aleatoric_uncertainty for r in results_by_sys["ASTRAHEAL"]]
    ax5.scatter(ep_uncs, al_uncs, color="#2ca02c", s=150, edgecolors="black", zorder=5)
    for i, sc in enumerate(scenarios):
        ax5.text(ep_uncs[i] + 0.02, al_uncs[i] + 0.01, sc.scenario_id, fontsize=8)
    ax5.axvline(0.50, color="red", linestyle="--", label="OOD Gating Threshold (0.50)")
    ax5.set_xlabel("Epistemic Uncertainty ($u_{epistemic}$)", fontweight="bold")
    ax5.set_ylabel("Aleatoric Uncertainty ($u_{aleatoric}$)", fontweight="bold")
    ax5.set_title("Figure 5: Evidential Uncertainty Distribution Across Controlled Scenarios", fontweight="bold", pad=12)
    ax5.legend()
    ax5.grid(True, linestyle=":", alpha=0.5)
    plt.tight_layout()
    plt.savefig(fig_dir / "05_uncertainty_vs_intervention.png", dpi=200)
    plt.close(fig5)

    # Figure 6: Communication Arbitration Outcomes
    fig6, ax6 = plt.subplots(figsize=(8, 4))
    comm_acts = [r.comm_decision for r in results_by_sys["ASTRAHEAL"]]
    ax6.barh(scen_ids, [1]*len(scen_ids), color=["#d62728" if c == "ACT_AUTONOMOUSLY" else "#1f77b4" for c in comm_acts], edgecolor="black")
    for i, c in enumerate(comm_acts):
        ax6.text(0.5, i, c, ha="center", va="center", color="white", fontweight="bold", fontsize=8)
    ax6.set_xlim(0, 1.1)
    ax6.set_xticks([])
    ax6.set_title("Figure 6: Communication Arbitration (Autonomous Action vs Ground Deferral)", fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(fig_dir / "06_communication_arbitration.png", dpi=200)
    plt.close(fig6)

    # Figure 7: Safety Governor Rejections Matrix
    fig7, ax7 = plt.subplots(figsize=(8, 5))
    gov_rejs = [r.governor_rejections for r in results_by_sys["ASTRAHEAL"]]
    ax7.bar(np.arange(len(scen_ids)), gov_rejs, color="#ef4444", edgecolor="black", width=0.55)
    ax7.set_ylabel("Candidate Actions Rejected by Governor", fontweight="bold")
    ax7.set_title("Figure 7: Safety Governor Proposal Rejections per Scenario", fontweight="bold", pad=12)
    ax7.set_xticks(np.arange(len(scen_ids)))
    ax7.set_xticklabels(scen_ids, rotation=25, ha="right", fontsize=8)
    ax7.grid(True, linestyle=":", alpha=0.5, axis="y")
    plt.tight_layout()
    plt.savefig(fig_dir / "07_safety_governor_rejection_matrix.png", dpi=200)
    plt.close(fig7)

    # Figure 8: Full Ablation Multi-Metric Radar/Bar Comparison
    fig8, ax8 = plt.subplots(figsize=(10, 5))
    df_abl = pd.DataFrame({
        "System": sys_labels,
        "Survival (%)": [summary_table[k]["survival_pct"] for k in systems],
        "Payload (%)": [summary_table[k]["mean_payload_retention_pct"] for k in systems],
        "Utility (x100)": [summary_table[k]["mean_mission_utility"] * 100 for k in systems]
    })
    df_abl.plot(x="System", y=["Survival (%)", "Payload (%)", "Utility (x100)"], kind="bar", ax=ax8, edgecolor="black")
    ax8.set_ylabel("Normalized Metric Score", fontweight="bold")
    ax8.set_title("Figure 8: Controlled Architectural Ablation Comparison", fontweight="bold", pad=12)
    ax8.grid(True, linestyle=":", alpha=0.5, axis="y")
    plt.tight_layout()
    plt.savefig(fig_dir / "08_ablation_comparison.png", dpi=200)
    plt.close(fig8)

    print(f"\n[✓] All 8 publication figures saved to: {fig_dir}")
    print("\n[✓] Stage 14 Controlled Recoverability Benchmark Completed.")


if __name__ == "__main__":
    run_controlled_experiment()
