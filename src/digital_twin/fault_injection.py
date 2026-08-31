"""Reproducible fault injection engine for spacecraft digital twin simulations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import numpy as np


class FaultType(str, Enum):
    """Catalog of injectible physical and sensor faults."""
    BATTERY_RESISTANCE_SPIKE = "BATTERY_RESISTANCE_SPIKE"
    SOLAR_STRING_FAULT = "SOLAR_STRING_FAULT"
    THERMAL_RUNAWAY = "THERMAL_RUNAWAY"
    PARASITIC_LOAD_SURGE = "PARASITIC_LOAD_SURGE"
    SENSOR_BIAS_DRIFT = "SENSOR_BIAS_DRIFT"


@dataclass
class InjectedFaultSpec:
    """Specification of a single simulated fault scenario."""
    fault_type: FaultType
    start_time_sec: float
    duration_sec: Optional[float] = None  # None = permanent until mission end
    severity: float = 1.0  # Normalized multiplier or intensity
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def is_active(self, current_time_sec: float) -> bool:
        """Check if fault is active at given simulation time."""
        if current_time_sec < self.start_time_sec:
            return False
        if self.duration_sec is not None:
            return current_time_sec <= (self.start_time_sec + self.duration_sec)
        return True


@dataclass
class ActiveFaultState:
    """Current combined fault effects for the physics step."""
    battery_resistance_multiplier: float = 1.0
    solar_string_health_factor: float = 1.0
    thermal_runaway_heat_w: float = 0.0
    parasitic_load_w: float = 0.0
    sensor_biases: Dict[str, float] = field(default_factory=dict)
    active_fault_names: List[str] = field(default_factory=list)


class FaultInjectionEngine:
    """Manages scheduled and stochastic fault injection with strict random seed reproducibility."""

    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed
        self.rng = np.random.RandomState(random_seed)
        self.fault_specs: List[InjectedFaultSpec] = []

    def clear(self) -> None:
        """Clear all registered fault specifications."""
        self.fault_specs.clear()

    def add_fault(self, spec: InjectedFaultSpec) -> None:
        """Register a new fault specification."""
        self.fault_specs.append(spec)

    def evaluate(self, current_time_sec: float) -> ActiveFaultState:
        """Compute aggregate fault parameters affecting the digital twin at timestamp t."""
        state = ActiveFaultState()

        for spec in self.fault_specs:
            if spec.is_active(current_time_sec):
                state.active_fault_names.append(spec.fault_type.value)

                if spec.fault_type == FaultType.BATTERY_RESISTANCE_SPIKE:
                    mult = spec.parameters.get("resistance_multiplier", 3.0 * spec.severity)
                    state.battery_resistance_multiplier *= mult

                elif spec.fault_type == FaultType.SOLAR_STRING_FAULT:
                    health = spec.parameters.get("remaining_health", max(0.0, 1.0 - 0.7 * spec.severity))
                    state.solar_string_health_factor = min(state.solar_string_health_factor, health)

                elif spec.fault_type == FaultType.THERMAL_RUNAWAY:
                    heat = spec.parameters.get("exothermic_heat_w", 60.0 * spec.severity)
                    state.thermal_runaway_heat_w += heat

                elif spec.fault_type == FaultType.PARASITIC_LOAD_SURGE:
                    extra_w = spec.parameters.get("extra_load_w", 150.0 * spec.severity)
                    state.parasitic_load_w += extra_w

                elif spec.fault_type == FaultType.SENSOR_BIAS_DRIFT:
                    channel = spec.parameters.get("channel", "voltage_v")
                    offset = spec.parameters.get("bias_offset", -3.5 * spec.severity)
                    state.sensor_biases[channel] = state.sensor_biases.get(channel, 0.0) + offset

        return state
