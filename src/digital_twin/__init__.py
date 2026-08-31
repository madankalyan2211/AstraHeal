"""Spacecraft Electrical Power System (EPS) digital twin package."""

from src.digital_twin.orbit_model import OrbitalEnvironmentModel, OrbitState
from src.digital_twin.solar_array import SolarArrayModel, SolarArrayTelemetry
from src.digital_twin.battery_model import SpacecraftBatteryPackModel, BatteryTelemetry
from src.digital_twin.power_distribution import (
    PowerDistributionUnit,
    PowerDistributionTelemetry,
    SpacecraftOperatingMode,
)
from src.digital_twin.fault_injection import (
    FaultInjectionEngine,
    InjectedFaultSpec,
    FaultType,
    ActiveFaultState,
)
from src.digital_twin.simulator import SpacecraftEPSDigitalTwin

__all__ = [
    "OrbitalEnvironmentModel",
    "OrbitState",
    "SolarArrayModel",
    "SolarArrayTelemetry",
    "SpacecraftBatteryPackModel",
    "BatteryTelemetry",
    "PowerDistributionUnit",
    "PowerDistributionTelemetry",
    "SpacecraftOperatingMode",
    "FaultInjectionEngine",
    "InjectedFaultSpec",
    "FaultType",
    "ActiveFaultState",
    "SpacecraftEPSDigitalTwin",
]
