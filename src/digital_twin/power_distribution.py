"""Spacecraft Power Distribution Unit (PDU), bus regulation, and subsystem loads."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class SpacecraftOperatingMode(str, Enum):
    """Spacecraft operational mission modes."""
    SAFE_MODE = "SAFE_MODE"
    STANDBY = "STANDBY"
    SCIENCE = "SCIENCE"
    TRANSMISSION = "TRANSMISSION"


@dataclass
class PowerDistributionTelemetry:
    """Instantaneous power distribution telemetry."""
    bus_voltage_v: float
    total_load_power_w: float
    total_load_current_a: float
    subsystem_power_breakdown_w: Dict[str, float]
    operating_mode: SpacecraftOperatingMode
    net_battery_power_w: float  # Positive = discharging battery, Negative = charging battery


class PowerDistributionUnit:
    """Manages subsystem loads, operating modes, and power bus balance."""

    def __init__(
        self,
        nominal_bus_voltage_v: float = 28.0,
        obc_base_w: float = 25.0,
        adcs_base_w: float = 45.0,
        ttc_rx_w: float = 15.0,
        ttc_tx_w: float = 80.0,
        heaters_w: float = 35.0,
        payload_standby_w: float = 10.0,
        payload_active_w: float = 120.0
    ):
        self.bus_nominal_v = nominal_bus_voltage_v
        self.obc_w = obc_base_w
        self.adcs_w = adcs_base_w
        self.ttc_rx_w = ttc_rx_w
        self.ttc_tx_w = ttc_tx_w
        self.heaters_w = heaters_w
        self.payload_standby_w = payload_standby_w
        self.payload_active_w = payload_active_w
        self.current_mode = SpacecraftOperatingMode.STANDBY

    def set_mode(self, mode: SpacecraftOperatingMode) -> None:
        """Switch spacecraft mission operating mode."""
        self.current_mode = mode

    def compute_subsystem_loads(
        self,
        heater_active: bool = False,
        injected_parasitic_load_w: float = 0.0
    ) -> Dict[str, float]:
        """Calculate power draw per subsystem given current operating mode."""
        loads = {"OBC": self.obc_w}

        if self.current_mode == SpacecraftOperatingMode.SAFE_MODE:
            loads["ADCS"] = 10.0  # Reduced pointing
            loads["TTC"] = self.ttc_rx_w
            loads["PAYLOAD"] = 0.0
            loads["HEATERS"] = self.heaters_w if heater_active else 0.0
        elif self.current_mode == SpacecraftOperatingMode.STANDBY:
            loads["ADCS"] = self.adcs_w
            loads["TTC"] = self.ttc_rx_w
            loads["PAYLOAD"] = self.payload_standby_w
            loads["HEATERS"] = self.heaters_w if heater_active else 0.0
        elif self.current_mode == SpacecraftOperatingMode.SCIENCE:
            loads["ADCS"] = self.adcs_w
            loads["TTC"] = self.ttc_rx_w
            loads["PAYLOAD"] = self.payload_active_w
            loads["HEATERS"] = self.heaters_w if heater_active else 0.0
        elif self.current_mode == SpacecraftOperatingMode.TRANSMISSION:
            loads["ADCS"] = self.adcs_w
            loads["TTC"] = self.ttc_tx_w
            loads["PAYLOAD"] = self.payload_standby_w
            loads["HEATERS"] = self.heaters_w if heater_active else 0.0

        if injected_parasitic_load_w > 0.0:
            loads["PARASITIC_SHORT"] = injected_parasitic_load_w

        return loads

    def balance_power_bus(
        self,
        solar_generation_w: float,
        battery_terminal_voltage_v: float,
        heater_active: bool = False,
        injected_parasitic_load_w: float = 0.0
    ) -> PowerDistributionTelemetry:
        """Calculate total load, net battery power, and battery current required to balance the bus."""
        loads = self.compute_subsystem_loads(
            heater_active=heater_active,
            injected_parasitic_load_w=injected_parasitic_load_w
        )
        total_load_w = sum(loads.values())

        # Net power demanded from battery: P_batt = P_load - P_solar
        net_battery_power_w = total_load_w - solar_generation_w
        
        bus_v = max(18.0, battery_terminal_voltage_v)
        total_load_i = total_load_w / bus_v

        return PowerDistributionTelemetry(
            bus_voltage_v=bus_v,
            total_load_power_w=total_load_w,
            total_load_current_a=total_load_i,
            subsystem_power_breakdown_w=loads,
            operating_mode=self.current_mode,
            net_battery_power_w=net_battery_power_w
        )
