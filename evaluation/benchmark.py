"""Tri-System benchmark evaluation runner comparing Baseline A, Baseline B, and AstraHeal."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from src.digital_twin.simulator import SpacecraftEPSDigitalTwin
from src.digital_twin.power_distribution import SpacecraftOperatingMode
from src.telemetry.preprocess import TelemetryPreprocessor
from src.anomaly.detector import StatisticalDetector
from src.diagnosis.engine import FaultDiagnosisEngine
from src.planner.recovery_planner import AutonomousRecoveryPlanner
from src.safety.safety_governor import DeterministicSafetyGovernor
from evaluation.scenarios import BenchmarkScenarioSpec, BenchmarkScenarioGenerator
from evaluation.metrics import ComparativeScenarioMetrics, BenchmarkSuiteSummary, BenchmarkMetricsCalculator


class TriSystemBenchmarkRunner:
    """Runs rigorous multi-scenario comparative evaluations across three distinct recovery paradigms."""

    def __init__(self, simulation_step_sec: float = 10.0):
        self.step_sec = simulation_step_sec
        self.preprocessor = TelemetryPreprocessor()
        self.governor = DeterministicSafetyGovernor()

    def run_single_scenario(
        self,
        system_type: str,  # "BASELINE_A", "BASELINE_B", "ASTRAHEAL"
        spec: BenchmarkScenarioSpec
    ) -> ComparativeScenarioMetrics:
        """Run a single scenario under the selected system architecture."""
        twin = SpacecraftEPSDigitalTwin(system_id=f"TEST-{system_type}", random_seed=spec.random_seed)
        twin.battery.soc = spec.initial_soc
        for f in spec.faults:
            twin.inject_fault(f)

        steps = int(spec.orbit_duration_sec / self.step_sec)
        detector = StatisticalDetector()
        fitted = False
        actions_executed = 0

        max_temp = 0.0
        min_volt = 100.0
        min_soc = 1.0
        hard_violations = 0

        frames = []
        action_triggered = False

        for i in range(steps):
            frame = twin.step(dt_sec=self.step_sec)
            frames.append(frame.to_dict())

            max_temp = max(max_temp, frame.temperature_c)
            min_volt = min(min_volt, frame.voltage_v)
            if frame.state_of_charge is not None:
                min_soc = min(min_soc, frame.state_of_charge)

            # Check hard constraint breaches
            if frame.temperature_c > 46.0:
                hard_violations += 1
            if frame.voltage_v < 22.0:
                hard_violations += 1
            if frame.state_of_charge is not None and frame.state_of_charge < 0.15:
                hard_violations += 1

            # Anomaly & Diagnosis cycle
            if not fitted and len(frames) >= 20:
                feat_df = self.preprocessor.extract_features(pd.DataFrame(frames))
                detector.fit(feat_df.iloc[:20])
                fitted = True

            if fitted and not action_triggered and len(frames) % 5 == 0:
                cur_df = self.preprocessor.extract_features(pd.DataFrame(frames[-20:]))
                rep = detector.detect_frame(cur_df.iloc[-1])

                if rep.is_anomaly and rep.anomaly_score >= 0.50:
                    action_triggered = True
                    actions_executed += 1

                    if system_type == "BASELINE_A":
                        # No recovery action taken
                        pass

                    elif system_type == "BASELINE_B":
                        # Immediate Blind Safe Mode rule
                        twin.pdu.set_mode(SpacecraftOperatingMode.SAFE_MODE)

                    elif system_type == "ASTRAHEAL":
                        # Full Counterfactual + Safety Governor Autonomous Planning
                        diag_engine = FaultDiagnosisEngine(primary_method="bayesian")
                        diag = diag_engine.diagnose_frame(rep, cur_df.iloc[-1])
                        planner = AutonomousRecoveryPlanner(governor=self.governor)
                        plan = planner.plan_recovery(twin, diag, horizon_sec=3000.0)
                        planner.execute_plan_on_twin(twin, plan)

        final_soc = float(twin.battery.soc)
        survived = (hard_violations == 0) and (final_soc > 0.05) and (max_temp < 60.0)

        # Average payload availability across scenario
        payload_pct = (twin.pdu.payload_active_w / 120.0) * 100.0

        # Usable energy margin
        usable_ah = max(0.0, (final_soc - 0.15) * twin.battery.capacity_actual_ah)
        energy_margin = usable_ah * 28.0

        return ComparativeScenarioMetrics(
            system_name=system_type,
            scenario_id=spec.scenario_id,
            scenario_name=spec.name,
            survived=survived,
            hard_constraint_violations_count=hard_violations,
            max_battery_temp_c=float(max_temp),
            min_bus_voltage_v=float(min_volt),
            min_soc=float(min_soc),
            final_soc=float(final_soc),
            payload_availability_pct=float(payload_pct),
            energy_margin_wh=float(energy_margin),
            autonomous_actions_executed=actions_executed
        )

    def run_full_suite(
        self,
        suite: Optional[List[BenchmarkScenarioSpec]] = None
    ) -> Dict[str, BenchmarkSuiteSummary]:
        """Execute full benchmark suite across all three systems."""
        scenarios = suite or BenchmarkScenarioGenerator.get_full_evaluation_suite()
        systems = ["BASELINE_A", "BASELINE_B", "ASTRAHEAL"]
        results_by_system: Dict[str, List[ComparativeScenarioMetrics]] = {s: [] for s in systems}

        for spec in scenarios:
            for sys_name in systems:
                res = self.run_single_scenario(sys_name, spec)
                results_by_system[sys_name].append(res)

        summaries = {}
        for sys_name, res_list in results_by_system.items():
            summaries[sys_name] = BenchmarkMetricsCalculator.aggregate_suite(sys_name, res_list)

        return summaries
