"""Tests for spacecraft power-system digital twin physics models and fault injection."""

import pytest
import numpy as np
import pandas as pd

from src.digital_twin.orbit_model import OrbitalEnvironmentModel
from src.digital_twin.solar_array import SolarArrayModel
from src.digital_twin.battery_model import SpacecraftBatteryPackModel
from src.digital_twin.power_distribution import PowerDistributionUnit, SpacecraftOperatingMode
from src.digital_twin.fault_injection import FaultInjectionEngine, InjectedFaultSpec, FaultType
from src.digital_twin.simulator import SpacecraftEPSDigitalTwin


def test_orbital_environment_model():
    """Verify orbit simulation cycles between eclipse and sunlight."""
    orbit = OrbitalEnvironmentModel(orbit_period_sec=5740.0, eclipse_fraction=0.36)
    
    # At t=100s, spacecraft should be in eclipse
    state_eclipse = orbit.step(100.0)
    assert not state_eclipse.is_sunlight
    assert state_eclipse.solar_flux_w_m2 == 0.0

    # At t=3000s, spacecraft should be in sunlight
    state_sun = orbit.step(3000.0)
    assert state_sun.is_sunlight
    assert state_sun.solar_flux_w_m2 > 1000.0


def test_solar_array_power_generation():
    """Verify solar array generation under sunlight vs eclipse and string degradation."""
    sa = SolarArrayModel(panel_area_m2=2.5, nominal_efficiency=0.28)
    
    # Sunlight full power
    telem_full = sa.step(dt_sec=1.0, solar_flux_w_m2=1361.0, is_sunlight=True, string_health_factor=1.0)
    assert telem_full.generation_power_w > 800.0
    
    # Degraded solar string (50% loss)
    telem_degraded = sa.step(dt_sec=1.0, solar_flux_w_m2=1361.0, is_sunlight=True, string_health_factor=0.5)
    assert abs(telem_degraded.generation_power_w - (telem_full.generation_power_w * 0.5)) < 10.0


def test_battery_electro_thermal_kinetics():
    """Verify battery discharge Coulomb counting and Joule heating."""
    batt = SpacecraftBatteryPackModel(nominal_capacity_ah=40.0, initial_soc=1.0)
    
    # Discharge at 10A for 360s (0.1 hours -> 1.0 Ah -> 2.5% SoC drop)
    for _ in range(360):
        telem = batt.step(dt_sec=1.0, current_load_a=10.0)

    assert telem.state_of_charge < 0.98
    assert telem.core_temperature_c > 20.0  # Joule heating occurred


def test_fault_injection_reproducibility():
    """Verify fault injection engine triggers accurately according to schedule."""
    engine = FaultInjectionEngine(random_seed=42)
    spec = InjectedFaultSpec(
        fault_type=FaultType.BATTERY_RESISTANCE_SPIKE,
        start_time_sec=500.0,
        duration_sec=300.0,
        parameters={"resistance_multiplier": 4.0}
    )
    engine.add_fault(spec)

    state_before = engine.evaluate(100.0)
    assert state_before.battery_resistance_multiplier == 1.0
    assert len(state_before.active_fault_names) == 0

    state_during = engine.evaluate(600.0)
    assert state_during.battery_resistance_multiplier == 4.0
    assert FaultType.BATTERY_RESISTANCE_SPIKE.value in state_during.active_fault_names

    state_after = engine.evaluate(900.0)
    assert state_after.battery_resistance_multiplier == 1.0


def test_digital_twin_simulation_batch():
    """Verify end-to-end simulation generates valid TelemetryBatch."""
    sim = SpacecraftEPSDigitalTwin(system_id="TEST-TWIN-01", random_seed=42)
    batch = sim.run_simulation(duration_sec=300.0, dt_sec=10.0)
    assert len(batch) == 30
    
    df = batch.to_dataframe()
    assert "voltage_v" in df.columns
    assert "current_a" in df.columns
    assert "temperature_c" in df.columns
    assert df["voltage_v"].between(20.0, 36.0).all()
