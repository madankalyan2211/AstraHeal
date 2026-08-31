"""Evaluation benchmark scenarios and adversarial stress test generator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np

from src.digital_twin.fault_injection import InjectedFaultSpec, FaultType


@dataclass
class BenchmarkScenarioSpec:
    """Specification of an adversarial or nominal evaluation mission scenario."""
    scenario_id: str
    name: str
    category: str  # "KNOWN", "COMPOUND_OOD", "ENVIRONMENTAL_STRESS", "SENSOR_CORRUPT"
    orbit_duration_sec: float = 12000.0  # ~2.1 LEO orbits
    faults: List[InjectedFaultSpec] = field(default_factory=list)
    initial_soc: float = 0.95
    random_seed: int = 42


class BenchmarkScenarioGenerator:
    """Generates standardized benchmark suites for comparative evaluation."""

    @staticmethod
    def get_full_evaluation_suite(random_seed: int = 42) -> List[BenchmarkScenarioSpec]:
        """Generate a diverse 8-scenario stress test matrix."""
        rng = np.random.RandomState(random_seed)
        suite = []

        # 1. Nominal Mission Run
        suite.append(BenchmarkScenarioSpec(
            scenario_id="SCEN-01-NOMINAL",
            name="Nominal 2-Orbit Baseline Mission",
            category="NOMINAL",
            faults=[],
            random_seed=random_seed + 1
        ))

        # 2. Known Battery Impedance Surge (Eclipse phase)
        suite.append(BenchmarkScenarioSpec(
            scenario_id="SCEN-02-BATT-SURGE",
            name="Battery Internal Resistance Surge (4.2x)",
            category="KNOWN",
            faults=[
                InjectedFaultSpec(fault_type=FaultType.BATTERY_RESISTANCE_SPIKE, start_time_sec=1200.0, parameters={"resistance_multiplier": 4.2})
            ],
            random_seed=random_seed + 2
        ))

        # 3. Known Thermal Runaway Initiation
        suite.append(BenchmarkScenarioSpec(
            scenario_id="SCEN-03-THERMAL-RUNAWAY",
            name="Exothermic Battery Thermal Runaway (120W)",
            category="KNOWN",
            faults=[
                InjectedFaultSpec(fault_type=FaultType.THERMAL_RUNAWAY, start_time_sec=2000.0, parameters={"exothermic_heat_w": 120.0})
            ],
            random_seed=random_seed + 3
        ))

        # 4. Known Solar String Partial Loss
        suite.append(BenchmarkScenarioSpec(
            scenario_id="SCEN-04-SOLAR-LOSS",
            name="Solar Array 60% String Occlusion",
            category="KNOWN",
            faults=[
                InjectedFaultSpec(fault_type=FaultType.SOLAR_STRING_FAULT, start_time_sec=3000.0, parameters={"remaining_health": 0.40})
            ],
            random_seed=random_seed + 4
        ))

        # 5. Compound Failure: Solar Loss + Parasitic Short
        suite.append(BenchmarkScenarioSpec(
            scenario_id="SCEN-05-COMPOUND",
            name="Compound Failure (Solar Loss + Parasitic Load)",
            category="COMPOUND_OOD",
            faults=[
                InjectedFaultSpec(fault_type=FaultType.SOLAR_STRING_FAULT, start_time_sec=2500.0, parameters={"remaining_health": 0.50}),
                InjectedFaultSpec(fault_type=FaultType.PARASITIC_LOAD_SURGE, start_time_sec=3500.0, parameters={"extra_load_w": 200.0})
            ],
            random_seed=random_seed + 5
        ))

        # 6. Environmental Stress: Low Initial SoC in Deep Eclipse
        suite.append(BenchmarkScenarioSpec(
            scenario_id="SCEN-06-LOW-SOC-ECLIPSE",
            name="Low Initial Reserve (35% SoC) with Resistance Spike",
            category="ENVIRONMENTAL_STRESS",
            initial_soc=0.35,
            faults=[
                InjectedFaultSpec(fault_type=FaultType.BATTERY_RESISTANCE_SPIKE, start_time_sec=800.0, parameters={"resistance_multiplier": 3.5})
            ],
            random_seed=random_seed + 6
        ))

        # 7. Extreme Novel Severity (12.0x Resistance Surge)
        suite.append(BenchmarkScenarioSpec(
            scenario_id="SCEN-07-EXTREME-SEVERITY",
            name="Extreme Novel Resistance Spike (12.0x)",
            category="COMPOUND_OOD",
            faults=[
                InjectedFaultSpec(fault_type=FaultType.BATTERY_RESISTANCE_SPIKE, start_time_sec=4000.0, parameters={"resistance_multiplier": 12.0})
            ],
            random_seed=random_seed + 7
        ))

        # 8. Corrupted Sensor Inversion
        suite.append(BenchmarkScenarioSpec(
            scenario_id="SCEN-08-SENSOR-CORRUPT",
            name="Telemetry Sensor Offset Inversion Glitch",
            category="SENSOR_CORRUPT",
            faults=[
                InjectedFaultSpec(fault_type=FaultType.SENSOR_BIAS_DRIFT, start_time_sec=1500.0, parameters={"bias_offset": -8.0, "channel": "voltage_v"})
            ],
            random_seed=random_seed + 8
        ))

        return suite
