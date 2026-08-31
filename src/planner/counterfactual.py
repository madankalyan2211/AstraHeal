"""Counterfactual simulation engine executing parallel, isolated recovery branch evaluations."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.diagnosis.schema import DiagnosisReport
from src.digital_twin.simulator import SpacecraftEPSDigitalTwin
from src.planner.actions import RecoveryAction, ActionGenerator
from src.planner.scenario import ScenarioResult, RiskMetrics, MissionImpact


class CounterfactualSimulator:
    """Simulates candidate recovery actions inside isolated digital twin branches.
    
    Guarantees:
    - Pure non-mutating branching: Base digital twin state is never modified.
    - Deterministic execution given identical seeds.
    - Comprehensive trajectory profiling across electrical, thermal, and mission dimensions.
    """

    def __init__(
        self,
        default_horizon_sec: float = 6000.0,  # ~1.05 LEO orbits
        simulation_step_sec: float = 10.0,
        max_temp_threshold_c: float = 48.0,
        min_voltage_threshold_v: float = 22.0,
        min_soc_threshold: float = 0.20
    ):
        self.default_horizon_sec = default_horizon_sec
        self.step_sec = simulation_step_sec
        self.max_temp_c = max_temp_threshold_c
        self.min_voltage_v = min_voltage_threshold_v
        self.min_soc = min_soc_threshold

    def evaluate_action(
        self,
        base_twin: SpacecraftEPSDigitalTwin,
        action: RecoveryAction,
        horizon_sec: Optional[float] = None
    ) -> ScenarioResult:
        """Clone the digital twin, execute the candidate action, and evaluate predicted outcome."""
        horizon = horizon_sec or self.default_horizon_sec
        
        # 1. Deep clone the twin to guarantee isolation
        cloned_twin = base_twin.clone()

        # Capture initial snapshot
        init_snap = {
            "time_sec": base_twin.current_time_sec,
            "voltage_v": base_twin.battery.compute_open_circuit_voltage(base_twin.battery.soc),
            "soc": base_twin.battery.soc,
            "temp_c": base_twin.battery.temp_core_c,
            "operating_mode": base_twin.pdu.current_mode.value,
            "payload_active_w": base_twin.pdu.payload_active_w
        }

        # 2. Apply action to the cloned twin
        action.apply_to_digital_twin(cloned_twin)

        # 3. Simulate forward across prediction horizon
        steps = int(horizon / self.step_sec)
        trajectory_records = []
        
        thermal_runaway = False
        voltage_collapse = False
        violations = []

        joule_heat_accum_kj = 0.0

        for _ in range(steps):
            frame = cloned_twin.step(dt_sec=self.step_sec)
            
            # Check hard physical failure triggers
            if frame.temperature_c > self.max_temp_c:
                thermal_runaway = True
                violations.append(f"Temperature breached hard limit ({frame.temperature_c:.1f}°C > {self.max_temp_c}°C)")

            if frame.voltage_v < self.min_voltage_v:
                voltage_collapse = True
                violations.append(f"Bus voltage collapsed below minimum threshold ({frame.voltage_v:.1f}V < {self.min_voltage_v}V)")

            if frame.state_of_charge is not None and frame.state_of_charge < self.min_soc:
                violations.append(f"Battery SoC depleted into critical reserve ({frame.state_of_charge*100:.1f}% < {self.min_soc*100:.1f}%)")

            # Accumulate Joule heat proxy
            r_int = cloned_twin.battery.r0_actual
            joule_heat_accum_kj += ((frame.current_a ** 2) * r_int * self.step_sec) / 1000.0

            trajectory_records.append({
                "time_sec": frame.timestamp,
                "voltage_v": frame.voltage_v,
                "current_a": frame.current_a,
                "temperature_c": frame.temperature_c,
                "soc": frame.state_of_charge,
                "solar_power_w": frame.metadata.get("solar_power_w", 0.0),
                "load_power_w": frame.metadata.get("load_power_w", 0.0)
            })

        traj_df = pd.DataFrame(trajectory_records)

        # 4. Compile Risk Metrics
        max_t = float(traj_df["temperature_c"].max())
        min_v = float(traj_df["voltage_v"].min())
        max_i = float(traj_df["current_a"].abs().max())
        min_soc = float(traj_df["soc"].min())
        final_soc = float(traj_df["soc"].iloc[-1])

        survived = not (thermal_runaway or voltage_collapse or final_soc <= 0.05)

        risk_metrics = RiskMetrics(
            max_battery_temp_c=max_t,
            min_bus_voltage_v=min_v,
            max_battery_current_a=max_i,
            min_state_of_charge=min_soc,
            final_state_of_charge=final_soc,
            cumulative_joule_heat_kj=float(joule_heat_accum_kj),
            thermal_runaway_triggered=thermal_runaway,
            voltage_collapse_triggered=voltage_collapse
        )

        # 5. Compile Mission Impact
        # Base nominal payload active power is 120W
        avail_frac = max(0.0, min(1.0, cloned_twin.pdu.payload_active_w / 120.0))
        disruption = action.estimated_implementation_cost
        rev_score = 1.0 if action.is_reversible else 0.0
        delta_soh = float(base_twin.battery.soh - cloned_twin.battery.soh)

        # Usable energy margin (Wh above 20% SoC floor)
        usable_ah = max(0.0, (final_soc - 0.20) * cloned_twin.battery.capacity_actual_ah)
        energy_margin_wh = usable_ah * 28.0

        mission_impact = MissionImpact(
            payload_availability_fraction=avail_frac,
            energy_margin_wh=energy_margin_wh,
            battery_degradation_delta_soh=delta_soh,
            reversibility_score=rev_score,
            disruption_penalty=disruption
        )

        final_snap = {
            "time_sec": cloned_twin.current_time_sec,
            "voltage_v": float(traj_df["voltage_v"].iloc[-1]),
            "soc": final_soc,
            "temp_c": float(traj_df["temperature_c"].iloc[-1]),
            "operating_mode": cloned_twin.pdu.current_mode.value,
            "payload_active_w": cloned_twin.pdu.payload_active_w
        }

        # Summary dict for quick analysis
        traj_summary = {
            "mean_temp_c": float(traj_df["temperature_c"].mean()),
            "mean_voltage_v": float(traj_df["voltage_v"].mean()),
            "final_soc": final_soc
        }

        return ScenarioResult(
            action=action,
            simulation_seed=base_twin.random_seed,
            duration_sec=horizon,
            survived=survived,
            risk_metrics=risk_metrics,
            mission_impact=mission_impact,
            constraint_violations=list(set(violations)),
            initial_snapshot=init_snap,
            predicted_final_snapshot=final_snap,
            status="COMPLETED",
            trajectory_summary=traj_summary
        )

    def evaluate_all(
        self,
        base_twin: SpacecraftEPSDigitalTwin,
        candidates: List[RecoveryAction],
        horizon_sec: Optional[float] = None
    ) -> List[ScenarioResult]:
        """Evaluate a full list of candidate recovery actions sequentially across independent clones."""
        results = []
        for action in candidates:
            res = self.evaluate_action(base_twin, action, horizon_sec=horizon_sec)
            results.append(res)
        return results
