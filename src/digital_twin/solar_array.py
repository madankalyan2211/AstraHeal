"""Photovoltaic solar array model with Maximum Power Point Tracking (MPPT) and thermal derating."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class SolarArrayTelemetry:
    """Instantaneous solar generation telemetry."""
    generation_power_w: float
    array_voltage_v: float
    array_current_a: float
    cell_temperature_c: float
    health_factor: float  # [0.0, 1.0] (1.0 = undamaged, <1.0 = partial string failure)


class SolarArrayModel:
    """Simulates spacecraft photovoltaic power generation under varying irradiance and temperature."""

    def __init__(
        self,
        panel_area_m2: float = 2.5,
        nominal_efficiency: float = 0.28,  # Triple-junction GaAs space solar cell
        mppt_efficiency: float = 0.95,
        temp_coefficient_pmax: float = -0.0035,  # -0.35%/°C above 25°C
        nominal_cell_temp_c: float = 25.0,
        thermal_time_constant_sec: float = 120.0
    ):
        self.area_m2 = panel_area_m2
        self.eff_nom = nominal_efficiency
        self.mppt_eff = mppt_efficiency
        self.temp_coeff = temp_coefficient_pmax
        self.t_ref_c = nominal_cell_temp_c
        self.tau_thermal = thermal_time_constant_sec
        self.cell_temp_c = 20.0

    def step(
        self,
        dt_sec: float,
        solar_flux_w_m2: float,
        is_sunlight: bool,
        bus_voltage_v: float = 28.0,
        string_health_factor: float = 1.0
    ) -> SolarArrayTelemetry:
        """Advance solar array state by dt and compute electrical power output."""
        # 1. Solar array equilibrium temperature model
        # In sunlight, solar panels reach ~55°C; in eclipse they cool toward -60°C
        t_target_c = (55.0 * (solar_flux_w_m2 / 1361.0)) if is_sunlight else -60.0
        alpha = 1.0 - math.exp(-dt_sec / self.tau_thermal) if hasattr(self, '_math') else min(1.0, dt_sec / self.tau_thermal)
        self.cell_temp_c += alpha * (t_target_c - self.cell_temp_c)

        # 2. Temperature derated efficiency
        temp_delta = self.cell_temp_c - self.t_ref_c
        eff_actual = self.eff_nom * (1.0 + self.temp_coeff * temp_delta)
        eff_actual = max(0.05, min(0.35, eff_actual))

        # 3. Maximum Electrical Power generated
        # P = Flux * Area * Efficiency * MPPT * String_Health
        p_ideal = solar_flux_w_m2 * self.area_m2 * eff_actual * self.mppt_eff
        p_actual = max(0.0, p_ideal * max(0.0, min(1.0, string_health_factor)))

        # 4. Array voltage and current delivered to power bus
        array_v = max(bus_voltage_v, 28.0)
        array_i = (p_actual / array_v) if array_v > 0.1 else 0.0

        return SolarArrayTelemetry(
            generation_power_w=p_actual,
            array_voltage_v=array_v,
            array_current_a=array_i,
            cell_temperature_c=self.cell_temp_c,
            health_factor=string_health_factor
        )
