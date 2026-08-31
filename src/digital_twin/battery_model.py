"""Spacecraft battery pack electro-thermal equivalent circuit model (Thevenin ECM)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class BatteryTelemetry:
    """Instantaneous battery pack telemetry."""
    terminal_voltage_v: float
    open_circuit_voltage_v: float
    current_a: float  # Positive = discharge, Negative = charge
    state_of_charge: float  # [0.0, 1.0]
    capacity_ah: float
    internal_resistance_ohm: float
    core_temperature_c: float
    state_of_health: float  # [0.0, 1.0]
    polarization_voltage_v: float


class SpacecraftBatteryPackModel:
    """Physics-based Li-ion spacecraft battery pack simulator with electro-thermal-aging coupling."""

    def __init__(
        self,
        nominal_capacity_ah: float = 40.0,
        initial_soc: float = 0.95,
        nominal_resistance_ohm: float = 0.045,
        cell_series_count: int = 8,
        thermal_mass_j_per_k: float = 4500.0,
        radiator_coupling_w_per_k: float = 1.2,
        chassis_temp_c: float = 20.0
    ):
        self.capacity_nom_ah = nominal_capacity_ah
        self.capacity_actual_ah = nominal_capacity_ah
        self.soc = max(0.0, min(1.0, initial_soc))
        self.r0_nom = nominal_resistance_ohm
        self.r0_actual = nominal_resistance_ohm
        self.n_series = cell_series_count
        
        # RC polarization parameters
        self.rp = 0.020
        self.cp = 2500.0  # Farads
        self.v_pol = 0.0  # Polarization voltage across RC pair

        # Thermal parameters
        self.c_th = thermal_mass_j_per_k
        self.h_rad = radiator_coupling_w_per_k
        self.t_chassis_c = chassis_temp_c
        self.temp_core_c = 20.0

        # Aging / degradation accumulators
        self.cumulative_ah_throughput = 0.0
        self.soh = 1.0

    def compute_open_circuit_voltage(self, soc: float) -> float:
        """Compute battery pack open circuit voltage as function of SoC."""
        # Single cell nominal NMC/LFP curve (series scaled by n_series=8 -> ~28V nominal)
        # V_cell(soc) = 3.4 + 0.7*soc - 0.2*(1-soc)^4 + 0.1*ln(soc + 1e-4)
        soc_clamped = max(1e-4, min(0.9999, soc))
        v_cell = (
            3.42 
            + 0.68 * soc_clamped 
            - 0.25 * ((1.0 - soc_clamped) ** 3) 
            + 0.04 * math.log(soc_clamped) 
            - 0.08 * math.exp(-25.0 * soc_clamped)
        )
        return float(v_cell * self.n_series)

    def step(
        self,
        dt_sec: float,
        current_load_a: float,  # Positive = discharge to bus, Negative = charge from solar
        ambient_temp_c: Optional[float] = None,
        injected_resistance_multiplier: float = 1.0,
        injected_capacity_fade_ratio: float = 0.0,
        injected_thermal_runaway_heat_w: float = 0.0
    ) -> BatteryTelemetry:
        """Advance battery state by dt_sec under specified electrical load and environmental conditions."""
        # 1. Update effective degradation parameters
        fade = min(0.40, injected_capacity_fade_ratio + 0.000005 * self.cumulative_ah_throughput)
        self.capacity_actual_ah = self.capacity_nom_ah * (1.0 - fade)
        self.soh = max(0.4, 1.0 - fade)
        
        # Internal resistance grows with aging + injected degradation multiplier
        self.r0_actual = self.r0_nom * (1.0 + 1.2 * fade) * injected_resistance_multiplier

        # 2. Charge regulation / Overcharge protection: if battery is full (SoC >= 1.0), taper charge current to 0
        effective_current_a = current_load_a
        if self.soc >= 1.0 and current_load_a < 0:
            effective_current_a = 0.0

        # Coulomb Counting for State of Charge (SoC)
        delta_soc = -(effective_current_a * dt_sec) / (self.capacity_actual_ah * 3600.0)
        self.soc = max(0.0, min(1.0, self.soc + delta_soc))
        self.cumulative_ah_throughput += abs(effective_current_a * dt_sec) / 3600.0

        # 3. Polarization RC Voltage step: dV_pol/dt = (I/Cp) - (V_pol / (Rp*Cp))
        tau_rc = self.rp * self.cp
        self.v_pol = self.v_pol * math.exp(-dt_sec / tau_rc) + (effective_current_a * self.rp) * (1.0 - math.exp(-dt_sec / tau_rc))

        # 4. Compute Open Circuit and Terminal Voltage
        voc = self.compute_open_circuit_voltage(self.soc)
        # V_terminal = Voc - I * R0 - V_pol
        v_terminal = voc - (effective_current_a * self.r0_actual) - self.v_pol
        v_terminal = max(16.0, min(36.0, v_terminal))  # Physical safety limits

        # 5. Electro-thermal balance
        # Joule heating Q_joule = I^2 * R0 + (V_pol^2 / Rp)
        q_joule = (effective_current_a ** 2) * self.r0_actual + ((self.v_pol ** 2) / max(1e-4, self.rp))
        
        # Exothermic runaway auto-acceleration if temperature exceeds 45°C
        q_exothermic = injected_thermal_runaway_heat_w
        if self.temp_core_c > 45.0:
            # Self-accelerating Arrhenius heat generation
            q_exothermic += 15.0 * math.exp(0.08 * (self.temp_core_c - 45.0))

        # Heat dissipation to chassis and space sink
        t_sink = ambient_temp_c if ambient_temp_c is not None else self.t_chassis_c
        q_loss = self.h_rad * (self.temp_core_c - t_sink)

        # dT/dt = (Q_joule + Q_exothermic - Q_loss) / C_th
        q_net = q_joule + q_exothermic - q_loss
        dt_temp = (q_net / self.c_th) * dt_sec
        self.temp_core_c = max(-40.0, min(120.0, self.temp_core_c + dt_temp))

        return BatteryTelemetry(
            terminal_voltage_v=v_terminal,
            open_circuit_voltage_v=voc,
            current_a=current_load_a,
            state_of_charge=self.soc,
            capacity_ah=self.capacity_actual_ah,
            internal_resistance_ohm=self.r0_actual,
            core_temperature_c=self.temp_core_c,
            state_of_health=self.soh,
            polarization_voltage_v=self.v_pol
        )
