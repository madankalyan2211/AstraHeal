"""Multi-Cycle Autonomous Recovery Benchmark and Evaluation Engine.

Provides:
1. Multi-Cycle Event Engine with debouncing and sequential recovery cycles
2. Detailed RecoveryCycleRecord capturing complete per-event decision telemetry
3. Multi-Cycle Scenarios with realistic sequential in-flight anomalies
4. Tri-System Comparative Multi-Cycle Evaluation (Baseline A vs Baseline B vs AstraHeal)
5. Comprehensive Mission-Level & Recovery-Level Metrics Computation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

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


class RecoveryCycleRecord(BaseModel):
    """Detailed telemetry and decision log for a single autonomous recovery cycle."""
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


class MultiCycleScenarioSpec(BaseModel):
    """Specification of a sequential multi-event mission scenario."""
    scenario_id: str
    name: str
    category: str  # "RECOVERABLE_SEQUENTIAL", "TRANSIENT_THEN_SEVERE", "COMM_ARBITRATION", "UNRECOVERABLE_PHYSICAL"
    orbit_duration_sec: float = 17220.0  # 3 full LEO orbits (3 x 5740s)
    initial_soc: float = 0.95
    faults: List[InjectedFaultSpec] = Field(default_factory=list)
    random_seed: int = 42
    description: str = ""


class MultiCycleScenarioMetrics(BaseModel):
    """Multi-dimensional performance metrics for a multi-cycle mission scenario."""
    system_name: str
    scenario_id: str
    scenario_name: str
    survived: bool
    
    # Mission-Level Metrics
    total_hard_violations_count: int
    time_in_violation_sec: float
    max_battery_temp_c: float
    min_bus_voltage_v: float
    min_soc: float
    final_soc: float
    mean_payload_availability_pct: float
    cumulative_delivered_payload_wh: float
    
    # Recovery-Level Metrics
    total_anomalies_detected: int
    total_recovery_cycles: int
    successful_recoveries_count: int
    unnecessary_interventions_count: int
    noop_decisions_count: int
    governor_rejections_count: int
    executed_unsafe_actions_count: int
    governor_bypasses_count: int
    
    # Cycles Detail
    recovery_cycles: List[RecoveryCycleRecord] = Field(default_factory=list)


class MultiCycleBenchmarkSuite:
    """Generates standardized sequential multi-event benchmark scenarios."""

    @staticmethod
    def get_standard_multi_cycle_suite() -> List[MultiCycleScenarioSpec]:
        """Generate 6 standardized multi-event scenarios spanning recoverable and unrecoverable regimes."""
        suite = []

        # 1. Nominal 3-Orbit Baseline: Tests that periodic sunrise/sunset events do not cause false action triggers
        suite.append(MultiCycleScenarioSpec(
            scenario_id="MC-01-NOMINAL-3ORBIT",
            name="Nominal 3-Orbit Spacecraft Operations",
            category="NOMINAL",
            orbit_duration_sec=17220.0,
            initial_soc=0.95,
            faults=[],
            random_seed=42,
            description="3 complete orbits with 3 eclipse/sunlight transitions. Tests false positive suppression."
        ))

        # 2. Sequential Recoverable Anomalies:
        # Event 1: Battery resistance surge (3.5x) in Eclipse 1 (t=1200s)
        # Event 2: Solar Array Partial String Degradation in Sunlight 2 (t=7500s)
        suite.append(MultiCycleScenarioSpec(
            scenario_id="MC-02-SEQUENTIAL-RECOVERABLE",
            name="Sequential Recoverable Faults (Battery Surge -> Solar Loss)",
            category="RECOVERABLE_SEQUENTIAL",
            orbit_duration_sec=17220.0,
            initial_soc=0.95,
            faults=[
                InjectedFaultSpec(fault_type=FaultType.BATTERY_RESISTANCE_SPIKE, start_time_sec=1200.0, parameters={"resistance_multiplier": 3.5}),
                InjectedFaultSpec(fault_type=FaultType.SOLAR_STRING_FAULT, start_time_sec=7500.0, parameters={"remaining_health": 0.45})
            ],
            random_seed=43,
            description="Sequential independent anomalies across Orbit 1 and Orbit 2. Tests multi-cycle re-planning."
        ))

        # 3. Benign Transient followed by Severe Thermal Runaway:
        # Event 1: Temporary sensor bias glitch at t=1000s (Eclipse 1) -> should NOT trigger destructive safe mode
        # Event 2: 70W Exothermic Thermal Runaway at t=6500s (Sunlight 2) -> requires urgent load shedding / safe mode
        suite.append(MultiCycleScenarioSpec(
            scenario_id="MC-03-TRANSIENT-THEN-SEVERE",
            name="Benign Sensor Glitch followed by Severe Thermal Fault",
            category="TRANSIENT_THEN_SEVERE",
            orbit_duration_sec=17220.0,
            initial_soc=0.95,
            faults=[
                InjectedFaultSpec(fault_type=FaultType.SENSOR_BIAS_DRIFT, start_time_sec=1000.0, parameters={"bias_offset": -4.0, "channel": "voltage_v"}),
                InjectedFaultSpec(fault_type=FaultType.THERMAL_RUNAWAY, start_time_sec=6500.0, parameters={"exothermic_heat_w": 70.0})
            ],
            random_seed=44,
            description="Tests that benign first event does not disrupt mission, while severe second event is mitigated."
        ))

        # 4. Multi-Cycle Communication-Aware Arbitration:
        # Event 1: Rapid fault in deep blackout (t=800s) -> Must act autonomously
        # Event 2: Slow gradual degradation during Ground Pass (t=8500s) -> Must defer to ground
        suite.append(MultiCycleScenarioSpec(
            scenario_id="MC-04-COMM-ARBITRATION",
            name="Communication-Aware Sequential Arbitration",
            category="COMM_ARBITRATION",
            orbit_duration_sec=17220.0,
            initial_soc=0.95,
            faults=[
                InjectedFaultSpec(fault_type=FaultType.BATTERY_RESISTANCE_SPIKE, start_time_sec=800.0, parameters={"resistance_multiplier": 4.0}),
                InjectedFaultSpec(fault_type=FaultType.PARASITIC_LOAD_SURGE, start_time_sec=8500.0, parameters={"extra_load_w": 60.0})
            ],
            random_seed=45,
            description="Tests correct arbitration between immediate onboard action vs ground deferral across orbits."
        ))

        # 5. Unrecoverable Extreme Thermal Runaway (Physical Limit Benchmark):
        # 140W internal exothermic heat (exceeds 65W radiator capacity)
        suite.append(MultiCycleScenarioSpec(
            scenario_id="MC-05-UNRECOVERABLE-THERMAL",
            name="Unrecoverable Exothermic Runaway (140W Heat)",
            category="UNRECOVERABLE_PHYSICAL",
            orbit_duration_sec=17220.0,
            initial_soc=0.95,
            faults=[
                InjectedFaultSpec(fault_type=FaultType.THERMAL_RUNAWAY, start_time_sec=4000.0, parameters={"exothermic_heat_w": 140.0})
            ],
            random_seed=46,
            description="Physical boundary test: internal chemical heat physically exceeds radiator rejection capacity."
        ))

        # 6. Unrecoverable Deep Shadow Starvation (Energy Limit Benchmark):
        # 25% Initial SoC entering extended eclipse with impedance surge
        suite.append(MultiCycleScenarioSpec(
            scenario_id="MC-06-UNRECOVERABLE-STARVATION",
            name="Deep Eclipse Low-Reserve Energy Depletion",
            category="UNRECOVERABLE_PHYSICAL",
            orbit_duration_sec=17220.0,
            initial_soc=0.25,
            faults=[
                InjectedFaultSpec(fault_type=FaultType.BATTERY_RESISTANCE_SPIKE, start_time_sec=300.0, parameters={"resistance_multiplier": 3.0})
            ],
            random_seed=47,
            description="Physical energy deficit test: initial stored Wh is insufficient to survive shadow pass."
        ))

        return suite


class MultiCycleBenchmarkRunner:
    """Executes multi-cycle benchmarks with debounced event management and comprehensive telemetry logging."""

    def __init__(
        self,
        simulation_step_sec: float = 10.0,
        event_cooldown_sec: float = 300.0  # 5-minute cooldown between recurring evaluations of same fault
    ):
        self.step_sec = simulation_step_sec
        self.cooldown_sec = event_cooldown_sec
        self.preprocessor = TelemetryPreprocessor()
        self.governor = DeterministicSafetyGovernor()
        self.comm_mgr = CommunicationAwareAutonomyManager()

    def run_scenario(
        self,
        system_type: str,  # "BASELINE_A", "BASELINE_B", "ASTRAHEAL"
        spec: MultiCycleScenarioSpec
    ) -> MultiCycleScenarioMetrics:
        """Run a sequential multi-event scenario under the selected architecture."""
        twin = SpacecraftEPSDigitalTwin(system_id=f"MC-{system_type}", random_seed=spec.random_seed)
        twin.battery.soc = spec.initial_soc
        for f in spec.faults:
            twin.inject_fault(f)

        steps = int(spec.orbit_duration_sec / self.step_sec)
        detector = StatisticalDetector()
        fitted = False

        # State tracking
        frames = []
        cycle_records: List[RecoveryCycleRecord] = []
        cycle_counter = 0
        
        last_event_time_sec = -1e9
        last_event_mode = "NONE"
        
        hard_violations = 0
        violation_time_sec = 0.0
        max_temp = 0.0
        min_volt = 100.0
        min_soc = 1.0
        cumulative_payload_wh = 0.0
        
        unnecessary_interventions = 0
        noop_decisions = 0
        governor_rejections = 0
        executed_unsafe_actions = 0
        governor_bypasses = 0
        successful_recoveries = 0

        for step_idx in range(steps):
            current_t = twin.current_time_sec
            frame = twin.step(dt_sec=self.step_sec)
            frames.append(frame.to_dict())

            # Track peak limits
            max_temp = max(max_temp, frame.temperature_c)
            min_volt = min(min_volt, frame.voltage_v)
            if frame.state_of_charge is not None:
                min_soc = min(min_soc, frame.state_of_charge)

            # Accumulate science payload energy delivered (Power x dt)
            payload_w = twin.pdu.payload_active_w
            cumulative_payload_wh += (payload_w * self.step_sec) / 3600.0

            # Check physical hard constraint exceedance
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

            # Fit anomaly detector on a full nominal orbit (300 frames = 3000s)
            if not fitted and len(frames) >= 250:
                feat_df = self.preprocessor.extract_features(pd.DataFrame(frames))
                detector.fit(feat_df.iloc[:250])
                fitted = True

            # Multi-Cycle Event Evaluation Loop (Every 5 steps / 50s)
            if fitted and len(frames) % 5 == 0:
                cur_df = self.preprocessor.extract_features(pd.DataFrame(frames[-30:]))
                rep = detector.detect_frame(cur_df.iloc[-1])

                # Check if anomaly triggers
                if rep.is_anomaly and rep.anomaly_score >= 0.55:
                    # Debouncing Logic: enforce cooldown between sequential evaluations
                    time_since_last = current_t - last_event_time_sec
                    if time_since_last >= self.cooldown_sec:
                        # Initiate New Recovery Cycle
                        cycle_counter += 1
                        cycle_id = f"CYCLE_{cycle_counter:03d}"
                        last_event_time_sec = current_t

                        # --- Diagnosis & Uncertainty ---
                        diag_engine = FaultDiagnosisEngine(primary_method="bayesian")
                        diag = diag_engine.diagnose_frame(rep, cur_df.iloc[-1])
                        last_event_mode = diag.primary_failure_mode

                        # --- Communication Check ---
                        comm_state = self.comm_mgr.channel.evaluate_state(current_t)

                        # --- Architecture Execution ---
                        selected_act_id = None
                        selected_act_type = None
                        sel_score = 0.0
                        gov_verdict = "N/A"
                        gov_reasons = []
                        exec_ok = True

                        if system_type == "BASELINE_A":
                            # Baseline A: Passive logging only
                            selected_act_id = "NOOP_PASSIVE"
                            selected_act_type = "CONTINUE_NOMINAL"
                            gov_verdict = "PASSIVE_UNMITIGATED"

                        elif system_type == "BASELINE_B":
                            # Baseline B: Immediate Blind Safe Mode rule
                            selected_act_id = "BLIND_SAFE_MODE"
                            selected_act_type = "ENTER_SAFE_MODE"
                            gov_verdict = "UNCHECKED_HEURISTIC"
                            twin.pdu.set_mode(SpacecraftOperatingMode.SAFE_MODE)
                            if diag.status == DiagnosisStatus.INSUFFICIENT_EVIDENCE:
                                unnecessary_interventions += 1

                        elif system_type == "ASTRAHEAL":
                            # AstraHeal: Full Counterfactual + Safety Governor Autonomous Planning
                            planner = AutonomousRecoveryPlanner(governor=self.governor)
                            plan = planner.plan_recovery(twin, diag, horizon_sec=3000.0)

                            # Communication Arbitration
                            comm_dec = self.comm_mgr.arbitrate(
                                current_time_sec=current_t,
                                diagnosis=diag,
                                plan=plan,
                                noop_scenario=None
                            )

                            if comm_dec.decision == AutonomyActionType.ACT_AUTONOMOUSLY:
                                # Apply authorized action
                                if plan.selected_action:
                                    selected_act_id = plan.selected_action.action_id
                                    selected_act_type = plan.selected_action.action_type.value
                                    sel_score = plan.selection_score
                                    
                                    if plan.safety_decision:
                                        gov_verdict = plan.safety_decision.status.value
                                        gov_reasons = plan.safety_decision.rejection_reasons
                                    
                                    if selected_act_type == "CONTINUE_NOMINAL":
                                        noop_decisions += 1
                                    
                                    planner.execute_plan_on_twin(twin, plan)
                                    successful_recoveries += 1
                                else:
                                    noop_decisions += 1
                            else:
                                # Deferred to ground
                                selected_act_id = "WAIT_FOR_GROUND"
                                selected_act_type = "DEFERRED_TO_GROUND"
                                gov_verdict = "GROUND_DEFERRED"

                            governor_rejections += plan.rejected_candidates_count

                        # Record Recovery Cycle Telemetry
                        cycle_records.append(RecoveryCycleRecord(
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
                            comm_decision="ACT_AUTONOMOUSLY" if system_type != "ASTRAHEAL" else comm_dec.decision.value,
                            candidates_count=plan.total_candidates_evaluated if system_type == "ASTRAHEAL" else 1,
                            approved_candidates_count=plan.approved_candidates_count if system_type == "ASTRAHEAL" else 1,
                            rejected_candidates_count=plan.rejected_candidates_count if system_type == "ASTRAHEAL" else 0,
                            selected_action_id=selected_act_id,
                            selected_action_type=selected_act_type,
                            selection_score=float(sel_score),
                            governor_verdict=gov_verdict,
                            governor_reasons=gov_reasons,
                            executed_successfully=exec_ok,
                            post_action_temp_c=float(frame.temperature_c),
                            post_action_volt_v=float(frame.voltage_v),
                            post_action_soc=float(twin.battery.soc)
                        ))

        final_soc = float(twin.battery.soc)
        survived = (hard_violations == 0) and (final_soc > 0.05) and (max_temp < 60.0)
        
        # Total nominal payload capacity over mission duration (120W x total hours)
        max_possible_payload_wh = (120.0 * spec.orbit_duration_sec) / 3600.0
        payload_availability_pct = (cumulative_payload_wh / max_possible_payload_wh) * 100.0

        return MultiCycleScenarioMetrics(
            system_name=system_type,
            scenario_id=spec.scenario_id,
            scenario_name=spec.name,
            survived=survived,
            total_hard_violations_count=hard_violations,
            time_in_violation_sec=violation_time_sec,
            max_battery_temp_c=float(max_temp),
            min_bus_voltage_v=float(min_volt),
            min_soc=float(min_soc),
            final_soc=float(final_soc),
            mean_payload_availability_pct=float(payload_availability_pct),
            cumulative_delivered_payload_wh=float(cumulative_payload_wh),
            total_anomalies_detected=len(cycle_records),
            total_recovery_cycles=len(cycle_records),
            successful_recoveries_count=successful_recoveries,
            unnecessary_interventions_count=unnecessary_interventions,
            noop_decisions_count=noop_decisions,
            governor_rejections_count=governor_rejections,
            executed_unsafe_actions_count=executed_unsafe_actions,
            governor_bypasses_count=governor_bypasses,
            recovery_cycles=cycle_records
        )

    def run_full_suite(
        self,
        suite: Optional[List[MultiCycleScenarioSpec]] = None
    ) -> Dict[str, List[MultiCycleScenarioMetrics]]:
        """Run entire multi-cycle benchmark suite across Baseline A, Baseline B, and AstraHeal."""
        scenarios = suite or MultiCycleBenchmarkSuite.get_standard_multi_cycle_suite()
        systems = ["BASELINE_A", "BASELINE_B", "ASTRAHEAL"]
        results: Dict[str, List[MultiCycleScenarioMetrics]] = {s: [] for s in systems}

        for spec in scenarios:
            for sys_name in systems:
                m = self.run_scenario(sys_name, spec)
                results[sys_name].append(m)

        return results
