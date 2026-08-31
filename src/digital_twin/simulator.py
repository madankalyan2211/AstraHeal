"""High-level spacecraft Electrical Power System (EPS) digital twin simulator."""

from __future__ import annotations

import copy
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from src.telemetry.schema import TelemetryBatch, TelemetryFrame, OperatingState
from src.digital_twin.orbit_model import OrbitalEnvironmentModel, OrbitState
from src.digital_twin.solar_array import SolarArrayModel, SolarArrayTelemetry
from src.digital_twin.battery_model import SpacecraftBatteryPackModel, BatteryTelemetry
from src.digital_twin.power_distribution import (
    PowerDistributionUnit,
    PowerDistributionTelemetry,
    SpacecraftOperatingMode,
)
from src.digital_twin.fault_injection import FaultInjectionEngine, InjectedFaultSpec, FaultType


class SpacecraftEPSDigitalTwin:
    """Physics-grade digital twin simulation for spacecraft Electrical Power Systems.
    
    Generates standardized telemetry adhering identically to the internal schema,
    enabling seamless validation of anomaly detectors, fault diagnosis engines,
    and counterfactual recovery branching.
    """

    def __init__(
        self,
        system_id: str = "ASTRA-SC-01",
        random_seed: int = 42,
        sensor_noise_sigma: float = 0.005
    ):
        self.system_id = system_id
        self.random_seed = random_seed
        self.sensor_noise_sigma = sensor_noise_sigma
        self.rng = np.random.RandomState(random_seed)

        # Physics sub-models
        self.orbit = OrbitalEnvironmentModel()
        self.solar_array = SolarArrayModel()
        self.battery = SpacecraftBatteryPackModel()
        self.pdu = PowerDistributionUnit()
        self.fault_injector = FaultInjectionEngine(random_seed=random_seed)

        self.current_time_sec = 0.0

    def clone(self) -> SpacecraftEPSDigitalTwin:
        """Create an independent deep copy of the digital twin state for counterfactual simulation.
        
        Guarantees that actions simulated on the clone will never mutate the baseline mission state.
        """
        cloned_twin = copy.deepcopy(self)
        return cloned_twin

    def reset(self, random_seed: Optional[int] = None) -> None:
        """Reset simulator state."""
        if random_seed is not None:
            self.random_seed = random_seed
            self.rng = np.random.RandomState(random_seed)
        self.battery = SpacecraftBatteryPackModel()
        self.solar_array = SolarArrayModel()
        self.pdu = PowerDistributionUnit()
        self.fault_injector = FaultInjectionEngine(random_seed=self.random_seed)
        self.current_time_sec = 0.0

    def inject_fault(self, spec: InjectedFaultSpec) -> None:
        """Register a fault for simulation."""
        self.fault_injector.add_fault(spec)

    def step(self, dt_sec: float = 1.0) -> TelemetryFrame:
        """Advance digital twin state by dt_sec and return a standardized TelemetryFrame."""
        t = self.current_time_sec

        # 1. Evaluate active injected faults
        faults = self.fault_injector.evaluate(t)

        # 2. Orbital environment (Sunlight / Eclipse & Flux)
        orbit_state = self.orbit.step(t)

        # 3. Solar array power generation
        solar_telem = self.solar_array.step(
            dt_sec=dt_sec,
            solar_flux_w_m2=orbit_state.solar_flux_w_m2,
            is_sunlight=orbit_state.is_sunlight,
            bus_voltage_v=self.battery.compute_open_circuit_voltage(self.battery.soc),
            string_health_factor=faults.solar_string_health_factor
        )

        # 4. Power distribution and bus balance
        pdu_telem = self.pdu.balance_power_bus(
            solar_generation_w=solar_telem.generation_power_w,
            battery_terminal_voltage_v=self.battery.compute_open_circuit_voltage(self.battery.soc),
            heater_active=(not orbit_state.is_sunlight and self.battery.temp_core_c < 10.0),
            injected_parasitic_load_w=faults.parasitic_load_w
        )

        # 5. Battery current demand (P_batt / V_bus)
        # Positive current = discharging battery; Negative = charging battery from solar surplus
        battery_current_demand_a = pdu_telem.net_battery_power_w / max(18.0, pdu_telem.bus_voltage_v)

        # 6. Step battery electro-thermal model
        battery_telem = self.battery.step(
            dt_sec=dt_sec,
            current_load_a=battery_current_demand_a,
            ambient_temp_c=(25.0 if orbit_state.is_sunlight else -20.0),
            injected_resistance_multiplier=faults.battery_resistance_multiplier,
            injected_thermal_runaway_heat_w=faults.thermal_runaway_heat_w
        )

        # 7. Apply sensor noise and sensor bias faults
        noise_v = self.rng.normal(0, self.sensor_noise_sigma * battery_telem.terminal_voltage_v)
        noise_i = self.rng.normal(0, self.sensor_noise_sigma * abs(battery_current_demand_a) + 0.005)
        noise_t = self.rng.normal(0, 0.05)

        meas_v = battery_telem.terminal_voltage_v + noise_v + faults.sensor_biases.get("voltage_v", 0.0)
        meas_i = battery_current_demand_a + noise_i + faults.sensor_biases.get("current_a", 0.0)
        meas_t = battery_telem.core_temperature_c + noise_t + faults.sensor_biases.get("temperature_c", 0.0)

        # 8. Determine operating health state
        op_state = OperatingState.NOMINAL
        if len(faults.active_fault_names) > 0:
            op_state = OperatingState.ANOMALOUS
        elif battery_telem.state_of_health < 0.70 or battery_telem.state_of_charge < 0.20:
            op_state = OperatingState.DEGRADED

        frame = TelemetryFrame(
            timestamp=t,
            system_id=self.system_id,
            subsystem="EPS",
            voltage_v=float(meas_v),
            current_a=float(meas_i),
            temperature_c=float(meas_t),
            capacity_ah=float(battery_telem.capacity_ah),
            state_of_charge=float(battery_telem.state_of_charge),
            health_indicators={
                "soh": float(battery_telem.state_of_health),
                "internal_resistance_ohm": float(battery_telem.internal_resistance_ohm),
                "solar_health_factor": float(solar_telem.health_factor)
            },
            operating_state=op_state,
            metadata={
                "is_sunlight": orbit_state.is_sunlight,
                "orbit_fraction": float(orbit_state.orbit_fraction),
                "solar_power_w": float(solar_telem.generation_power_w),
                "load_power_w": float(pdu_telem.total_load_power_w),
                "operating_mode": pdu_telem.operating_mode.value,
                "fault_active": len(faults.active_fault_names) > 0,
                "active_faults": faults.active_fault_names,
                "dataset": "ASTRA_SIMULATED_EPS"
            }
        )

        self.current_time_sec += dt_sec
        return frame

    def run_simulation(
        self,
        duration_sec: float = 18000.0,  # ~3.1 orbits
        dt_sec: float = 1.0,
        output_csv_path: Optional[Union[str, Path]] = None
    ) -> TelemetryBatch:
        """Run full continuous time-stepping simulation and compile into TelemetryBatch."""
        steps = int(duration_sec / dt_sec)
        batch = TelemetryBatch()

        for _ in range(steps):
            frame = self.step(dt_sec=dt_sec)
            batch.append(frame)

        if output_csv_path is not None:
            out_path = Path(output_csv_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            df = batch.to_dataframe()
            df.to_csv(out_path, index=False)

        return batch
