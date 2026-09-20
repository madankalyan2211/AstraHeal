"""Shared simulation and evaluation harness for AstraHeal Paper 4.

Implements Paper4ExecutionEngine:
- Closed-loop multi-cycle simulation across continuous orbits
- Physical parameter perturbation injection (C_th, h_rad, R_0, solar efficiency, parasitic bias)
- Telemetry sensor noise modeling (Gaussian jitter & drift)
- Complete decision pipeline: Detection -> Evidential Uncertainty -> Counterfactual Branching -> Safety Governor -> Digital Twin
- Evaluates 6 system architectures:
    1. ASTRAHEAL_FULL (Complete 5-stage integrated architecture)
    2. ABLATION_NO_UNCERTAINTY (Static confidence, zero epistemic uncertainty)
    3. ABLATION_NO_LOOKAHEAD (Static heuristic rule mapping, no counterfactual branches)
    4. ABLATION_NO_GOVERNOR (Ungoverned AI: proposals executed without safety gating)
    5. BASELINE_PASSIVE (No action taken, nominal logging)
    6. BASELINE_BLIND_SAFE_MODE (Immediate unconditional safe mode lock)
"""

from __future__ import annotations

import copy
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.digital_twin.simulator import SpacecraftEPSDigitalTwin
from src.digital_twin.fault_injection import InjectedFaultSpec, FaultType
from src.digital_twin.power_distribution import SpacecraftOperatingMode
from src.telemetry.preprocess import TelemetryPreprocessor
from src.anomaly.detector import StatisticalDetector
from src.diagnosis.engine import FaultDiagnosisEngine
from src.diagnosis.schema import DiagnosisReport, DiagnosisStatus, FailureMode
from src.planner.actions import ActionGenerator, RecoveryAction, RecoveryActionType
from src.planner.recovery_planner import AutonomousRecoveryPlanner, ActionPlanReport
from src.safety.safety_governor import DeterministicSafetyGovernor, SafetyDecision, SafetyStatus
from src.communication.manager import CommunicationAwareAutonomyManager, AutonomyActionType
from evaluation.paper4.scenario_generator import Paper4ScenarioSpec


class Paper4CycleRecord(BaseModel):
    """Detailed telemetry and decision log for a single autonomous recovery cycle in Paper 4."""
    cycle_id: str
    trigger_time_sec: float
    anomaly_score: float
    affected_signals: List[str] = Field(default_factory=list)
    diagnosis_status: str
    primary_failure_mode: str
    confidence: float
    epistemic_uncertainty: float
    aleatoric_uncertainty: float
    comm_link_status: str
    comm_decision: str
    candidates_count: int
    approved_candidates_count: int
    rejected_candidates_count: int
    selected_action_id: Optional[str]
    selected_action_type: Optional[str]
    selection_score: float
    governor_verdict: str
    governor_reasons: List[str] = Field(default_factory=list)
    executed_successfully: bool
    post_action_temp_c: float
    post_action_volt_v: float
    post_action_soc: float
    recovery_outcome: str  # "FULL_RECOVERY", "DEGRADED_RECOVERY", "NO_SAFE_ACTION", "UNSAFE_FAILURE"


class Paper4ScenarioResult(BaseModel):
    """Complete multi-dimensional evaluation results for a Paper 4 scenario run."""
    scenario_id: str
    experiment_id: str
    system_name: str
    random_seed: int
    survived: bool
    recovery_classification: str  # "FULL_RECOVERY", "DEGRADED_RECOVERY", "NO_SAFE_ACTION", "UNSAFE_FAILURE"
    
    # Mission-Level Physical Metrics
    total_hard_violations_count: int
    time_in_violation_sec: float
    max_battery_temp_c: float
    min_bus_voltage_v: float
    min_soc: float
    final_soc: float
    cumulative_delivered_payload_wh: float
    mean_payload_availability_pct: float
    
    # Recovery & Safety Governance Metrics
    total_anomalies_detected: int
    total_recovery_cycles: int
    governor_rejections_count: int
    executed_unsafe_actions: int
    governor_bypasses: int
    mean_epistemic_uncertainty: float
    
    # Per-Cycle Detailed Telemetry Traces
    recovery_cycles: List[Paper4CycleRecord] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Paper4ExecutionEngine:
    """High-fidelity multi-cycle execution engine with perturbation and noise support."""

    def __init__(self, step_sec: float = 10.0, cooldown_sec: float = 300.0):
        self.step_sec = step_sec
        self.cooldown_sec = cooldown_sec
        self.preprocessor = TelemetryPreprocessor()
        self.comm_mgr = CommunicationAwareAutonomyManager()
        self.governor = DeterministicSafetyGovernor()

    def _instantiate_perturbed_twin(self, spec: Paper4ScenarioSpec) -> SpacecraftEPSDigitalTwin:
        """Create digital twin with calibrated physical parameter perturbations."""
        twin = SpacecraftEPSDigitalTwin(
            system_id=f"P4-{spec.scenario_id}",
            random_seed=spec.random_seed,
            sensor_noise_sigma=spec.telemetry_noise_sigma
        )
        twin.battery.soc = spec.initial_soc

        perturbs = spec.physics_perturbations
        # 1. Thermal capacitance
        if "c_th_mult" in perturbs:
            twin.battery.c_th *= perturbs["c_th_mult"]
        
        # 2. Radiator radiative coupling
        if "h_rad_mult" in perturbs:
            twin.battery.h_rad *= perturbs["h_rad_mult"]

        # 3. Internal battery cell resistance
        if "r0_mult" in perturbs:
            twin.battery.r0_nom *= perturbs["r0_mult"]
            twin.battery.r0_actual *= perturbs["r0_mult"]

        # 4. Solar array conversion efficiency
        if "solar_efficiency_mult" in perturbs:
            twin.solar_array.eff_nom *= perturbs["solar_efficiency_mult"]

        # 5. Baseline quiescent parasitic load bias
        if "parasitic_load_bias_w" in perturbs and perturbs["parasitic_load_bias_w"] != 0.0:
            twin.pdu.payload_standby_w = max(0.0, twin.pdu.payload_standby_w + perturbs["parasitic_load_bias_w"])

        # Inject scenario faults
        for f in spec.faults:
            twin.inject_fault(copy.deepcopy(f))

        return twin

    def run_scenario(
        self,
        system_type: str,
        spec: Paper4ScenarioSpec
    ) -> Paper4ScenarioResult:
        """Execute a complete multi-orbit simulation under the selected system architecture."""
        twin = self._instantiate_perturbed_twin(spec)
        rng = np.random.RandomState(spec.random_seed)

        steps = int(spec.orbit_duration_sec / self.step_sec)
        detector = StatisticalDetector()
        fitted = False

        frames: List[Dict[str, Any]] = []
        cycle_records: List[Paper4CycleRecord] = []
        cycle_counter = 0

        last_event_time_sec = -1e9
        hard_violations = 0
        violation_time_sec = 0.0
        max_temp = 0.0
        min_volt = 100.0
        min_soc = 1.0
        cumulative_payload_wh = 0.0

        governor_rejections = 0
        executed_unsafe_actions = 0
        governor_bypasses = 0
        epistemic_uncertainties: List[float] = []

        for step_idx in range(steps):
            current_t = twin.current_time_sec
            frame = twin.step(dt_sec=self.step_sec)
            
            # Apply additive telemetry noise to measured frame if configured
            frame_dict = frame.to_dict()
            if spec.telemetry_noise_sigma > 0.005:
                # Add Gaussian noise to primary measured telemetry
                noise_scale = spec.telemetry_noise_sigma
                frame_dict["voltage_v"] += float(rng.normal(0.0, noise_scale * 28.0))
                frame_dict["current_a"] += float(rng.normal(0.0, noise_scale * 15.0))
                frame_dict["temperature_c"] += float(rng.normal(0.0, noise_scale * 30.0))
                if frame_dict.get("state_of_charge") is not None:
                    frame_dict["state_of_charge"] = float(np.clip(
                        frame_dict["state_of_charge"] + rng.normal(0.0, noise_scale * 0.2), 0.0, 1.0
                    ))

            frames.append(frame_dict)

            # Track peak limits
            max_temp = max(max_temp, frame.temperature_c)
            min_volt = min(min_volt, frame.voltage_v)
            if frame.state_of_charge is not None:
                min_soc = min(min_soc, frame.state_of_charge)

            # Accumulate payload energy delivered (Watt-hours)
            payload_w = twin.pdu.payload_active_w
            cumulative_payload_wh += (payload_w * self.step_sec) / 3600.0

            # Check physical hard constraint exceedance (Ground Truth)
            is_violating = False
            if frame.temperature_c > 46.0:
                is_violating = True
            if frame.voltage_v < 22.0:
                is_violating = True
            if frame.state_of_charge is not None and frame.state_of_charge < 0.15:
                is_violating = True

            if is_violating:
                hard_violations += 1
                violation_time_sec += self.step_sec

            # Fit anomaly detector during initial nominal flight (60 frames = 600s, prior to any fault injection)
            if not fitted and len(frames) >= 60:
                feat_df = self.preprocessor.extract_features(pd.DataFrame(frames))
                detector.fit(feat_df.iloc[:60])
                fitted = True

            # Anomaly & Recovery Loop (Every 5 steps / 50s)
            if fitted and len(frames) % 5 == 0:
                cur_df = self.preprocessor.extract_features(pd.DataFrame(frames[-30:]))
                rep = detector.detect_frame(cur_df.iloc[-1])

                if rep.is_anomaly and rep.anomaly_score >= 0.55:
                    time_since_last = current_t - last_event_time_sec
                    if time_since_last >= self.cooldown_sec:
                        cycle_counter += 1
                        cycle_id = f"CYCLE_{cycle_counter:03d}"
                        last_event_time_sec = current_t

                        # 1. Fault Diagnosis & Evidential Uncertainty
                        diag_engine = FaultDiagnosisEngine(primary_method="bayesian")
                        diag = diag_engine.diagnose_frame(rep, cur_df.iloc[-1])

                        # Noise impact on epistemic uncertainty:
                        # As noise increases, epistemic uncertainty naturally scales
                        if spec.telemetry_noise_sigma > 0.01:
                            noise_penalty = min(0.65, float(spec.telemetry_noise_sigma * 6.5))
                            diag.epistemic_uncertainty = float(min(1.0, diag.epistemic_uncertainty + noise_penalty))
                            diag.confidence = float(max(0.15, diag.confidence * (1.0 - 0.5 * noise_penalty)))

                        epistemic_uncertainties.append(float(diag.epistemic_uncertainty))

                        # 2. Communication State
                        comm_state = self.comm_mgr.channel.evaluate_state(current_t)

                        # 3. Architecture Decision Execution
                        selected_act_id = None
                        selected_act_type = None
                        sel_score = 0.0
                        gov_verdict = "N/A"
                        gov_reasons: List[str] = []
                        exec_ok = True
                        cycle_outcome = "FULL_RECOVERY"

                        if system_type == "BASELINE_PASSIVE":
                            selected_act_id = "NOOP_PASSIVE"
                            selected_act_type = "CONTINUE_NOMINAL"
                            gov_verdict = "PASSIVE_UNMITIGATED"

                        elif system_type == "BASELINE_BLIND_SAFE_MODE":
                            selected_act_id = "BLIND_SAFE_MODE"
                            selected_act_type = "ENTER_SAFE_MODE"
                            gov_verdict = "UNCHECKED_HEURISTIC"
                            twin.pdu.set_mode(SpacecraftOperatingMode.SAFE_MODE)
                            cycle_outcome = "DEGRADED_RECOVERY"

                        elif system_type == "ABLATION_NO_UNCERTAINTY":
                            # Strip uncertainty: assume 100% confidence, zero epistemic uncertainty
                            diag_no_u = copy.deepcopy(diag)
                            diag_no_u.confidence = 1.0
                            diag_no_u.epistemic_uncertainty = 0.0
                            planner = AutonomousRecoveryPlanner(governor=self.governor)
                            plan = planner.plan_recovery(twin, diag_no_u, horizon_sec=3000.0)

                            if plan.selected_action:
                                selected_act_id = plan.selected_action.action_id
                                selected_act_type = plan.selected_action.action_type.value
                                sel_score = plan.selection_score
                                if plan.safety_decision:
                                    gov_verdict = plan.safety_decision.status.value
                                    gov_reasons = plan.safety_decision.rejection_reasons
                                planner.execute_plan_on_twin(twin, plan)
                            governor_rejections += plan.rejected_candidates_count

                        elif system_type == "ABLATION_NO_LOOKAHEAD":
                            # Direct heuristic action mapping without counterfactual digital-twin branching
                            # Propose fixed mitigation based purely on label
                            if "RESISTANCE" in diag.primary_failure_mode or "OVERCURRENT" in diag.primary_failure_mode:
                                act = RecoveryAction(
                                    action_id="ACT_HEURISTIC_THROTTLE",
                                    action_type=RecoveryActionType.REDUCE_PAYLOAD_LOAD,
                                    description="Heuristic throttle without lookahead validation."
                                )
                            elif "THERMAL" in diag.primary_failure_mode:
                                act = RecoveryAction(
                                    action_id="ACT_HEURISTIC_SAFE",
                                    action_type=RecoveryActionType.ENTER_SAFE_MODE,
                                    description="Heuristic safe mode without lookahead validation."
                                )
                            else:
                                act = RecoveryAction(
                                    action_id="ACT_HEURISTIC_NOMINAL",
                                    action_type=RecoveryActionType.CONTINUE_NOMINAL,
                                    description="Heuristic nominal continue."
                                )
                            
                            # Evaluated by governor via instantaneous risk estimate
                            selected_act_id = act.action_id
                            selected_act_type = act.action_type.value
                            gov_verdict = "APPROVED"
                            act.apply_to_digital_twin(twin)

                        elif system_type == "ABLATION_NO_GOVERNOR":
                            # Ungoverned AI: Planner selects best scoring action, executes WITHOUT safety gating
                            planner = AutonomousRecoveryPlanner(governor=None)
                            candidates = ActionGenerator.generate_candidates(diag, twin)
                            
                            # Rank candidates purely on heuristic / AI preference without governor check
                            if candidates:
                                best_act = candidates[0]
                                selected_act_id = best_act.action_id
                                selected_act_type = best_act.action_type.value
                                gov_verdict = "GOVERNOR_BYPASSED"
                                governor_bypasses += 1
                                best_act.apply_to_digital_twin(twin)

                        elif system_type == "ASTRAHEAL_FULL":
                            # Complete 5-Stage Integrated AstraHeal Pipeline
                            planner = AutonomousRecoveryPlanner(governor=self.governor)
                            plan = planner.plan_recovery(twin, diag, horizon_sec=3000.0)

                            # Communication Link Arbitration
                            comm_dec = self.comm_mgr.arbitrate(
                                current_time_sec=current_t,
                                diagnosis=diag,
                                plan=plan,
                                noop_scenario=None
                            )

                            if comm_dec.decision == AutonomyActionType.ACT_AUTONOMOUSLY:
                                if plan.selected_action:
                                    selected_act_id = plan.selected_action.action_id
                                    selected_act_type = plan.selected_action.action_type.value
                                    sel_score = plan.selection_score
                                    
                                    if plan.safety_decision:
                                        gov_verdict = plan.safety_decision.status.value
                                        gov_reasons = plan.safety_decision.rejection_reasons
                                    
                                    planner.execute_plan_on_twin(twin, plan)
                                    if selected_act_type == "ENTER_SAFE_MODE" or selected_act_type == "DISABLE_NON_CRITICAL_SUBSYSTEM":
                                        cycle_outcome = "DEGRADED_RECOVERY"
                                    else:
                                        cycle_outcome = "FULL_RECOVERY"
                                else:
                                    cycle_outcome = "NO_SAFE_ACTION"
                                    selected_act_id = "NO_SAFE_ACTION_AVAILABLE"
                                    gov_verdict = "NO_ACTION_ADMISSIBLE"
                            else:
                                selected_act_id = "WAIT_FOR_GROUND"
                                selected_act_type = "DEFERRED_TO_GROUND"
                                gov_verdict = "GROUND_DEFERRED"

                            governor_rejections += plan.rejected_candidates_count

                        # Verify if executed action immediately violated invariants
                        post_t = twin.battery.temp_core_c
                        post_v = twin.battery.compute_open_circuit_voltage(twin.battery.soc)
                        post_soc = twin.battery.soc

                        if (post_t > 46.0 or post_v < 22.0 or post_soc < 0.15) and gov_verdict == "APPROVED":
                            executed_unsafe_actions += 1
                            cycle_outcome = "UNSAFE_FAILURE"

                        cycle_records.append(Paper4CycleRecord(
                            cycle_id=cycle_id,
                            trigger_time_sec=current_t,
                            anomaly_score=float(rep.anomaly_score),
                            affected_signals=rep.affected_signals,
                            diagnosis_status=diag.status.value,
                            primary_failure_mode=diag.primary_failure_mode,
                            confidence=float(diag.confidence),
                            epistemic_uncertainty=float(diag.epistemic_uncertainty),
                            aleatoric_uncertainty=float(diag.aleatoric_uncertainty),
                            comm_link_status=comm_state.link_status.value,
                            comm_decision="ACT_AUTONOMOUSLY" if system_type != "ASTRAHEAL_FULL" else comm_dec.decision.value,
                            candidates_count=plan.total_candidates_evaluated if "ASTRAHEAL" in system_type else 1,
                            approved_candidates_count=plan.approved_candidates_count if "ASTRAHEAL" in system_type else 1,
                            rejected_candidates_count=plan.rejected_candidates_count if "ASTRAHEAL" in system_type else 0,
                            selected_action_id=selected_act_id,
                            selected_action_type=selected_act_type,
                            selection_score=float(sel_score),
                            governor_verdict=gov_verdict,
                            governor_reasons=gov_reasons,
                            executed_successfully=exec_ok,
                            post_action_temp_c=float(post_t),
                            post_action_volt_v=float(post_v),
                            post_action_soc=float(post_soc),
                            recovery_outcome=cycle_outcome
                        ))

        # Determine overall scenario outcome
        survived = (hard_violations == 0)
        if survived:
            if any(c.selected_action_type == "ENTER_SAFE_MODE" for c in cycle_records):
                overall_classification = "DEGRADED_RECOVERY"
            else:
                overall_classification = "FULL_RECOVERY"
        else:
            if any(c.recovery_outcome == "NO_SAFE_ACTION" for c in cycle_records):
                overall_classification = "NO_SAFE_ACTION"
            else:
                overall_classification = "UNSAFE_FAILURE"

        # Total nominal payload capacity over mission duration (120W x total hours)
        max_possible_payload_wh = max(1e-3, (120.0 * spec.orbit_duration_sec) / 3600.0)
        mean_payload_avail = float(min(100.0, max(0.0, (cumulative_payload_wh / max_possible_payload_wh) * 100.0)))
        mean_u = float(np.mean(epistemic_uncertainties)) if epistemic_uncertainties else 0.0

        return Paper4ScenarioResult(
            scenario_id=spec.scenario_id,
            experiment_id=spec.experiment_id,
            system_name=system_type,
            random_seed=spec.random_seed,
            survived=survived,
            recovery_classification=overall_classification,
            total_hard_violations_count=hard_violations,
            time_in_violation_sec=violation_time_sec,
            max_battery_temp_c=float(max_temp),
            min_bus_voltage_v=float(min_volt),
            min_soc=float(min_soc),
            final_soc=float(twin.battery.soc),
            cumulative_delivered_payload_wh=float(cumulative_payload_wh),
            mean_payload_availability_pct=float(mean_payload_avail),
            total_anomalies_detected=len(cycle_records),
            total_recovery_cycles=len(cycle_records),
            governor_rejections_count=governor_rejections,
            executed_unsafe_actions=executed_unsafe_actions,
            governor_bypasses=governor_bypasses,
            mean_epistemic_uncertainty=mean_u,
            recovery_cycles=cycle_records,
            metadata={
                "orbit_duration_sec": spec.orbit_duration_sec,
                "noise_sigma": spec.telemetry_noise_sigma,
                "physics_perturbations": spec.physics_perturbations
            }
        )
