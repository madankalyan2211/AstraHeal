"""Orbital mechanics and solar irradiance model for Low Earth Orbit (LEO) spacecraft."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass
class OrbitState:
    """Instantaneous orbital environment state."""
    time_sec: float
    orbit_fraction: float  # [0.0, 1.0] across single orbit
    is_sunlight: bool
    solar_flux_w_m2: float
    sun_incidence_angle_deg: float


class OrbitalEnvironmentModel:
    """Simulates LEO spacecraft illumination conditions and solar flux transitions."""

    def __init__(
        self,
        altitude_km: float = 550.0,
        orbit_period_sec: float = 5740.0,  # ~95.6 min
        eclipse_fraction: float = 0.36,   # ~34.4 min eclipse
        solar_constant_w_m2: float = 1361.0,
        penumbra_transition_sec: float = 20.0
    ):
        self.altitude_km = altitude_km
        self.orbit_period_sec = orbit_period_sec
        self.eclipse_fraction = eclipse_fraction
        self.solar_constant_w_m2 = solar_constant_w_m2
        self.penumbra_transition_sec = penumbra_transition_sec

    def step(self, time_sec: float) -> OrbitState:
        """Compute solar illumination and incidence at elapsed mission time."""
        t_in_orbit = time_sec % self.orbit_period_sec
        orbit_fraction = t_in_orbit / self.orbit_period_sec

        # Eclipse occurs during the first fraction of orbit (in Earth's shadow)
        eclipse_duration = self.orbit_period_sec * self.eclipse_fraction
        
        if t_in_orbit < (eclipse_duration - self.penumbra_transition_sec):
            # Full umbra (Eclipse)
            is_sunlight = False
            flux = 0.0
            incidence_deg = 90.0
        elif t_in_orbit < eclipse_duration:
            # Penumbra exit transition
            fraction_exit = (t_in_orbit - (eclipse_duration - self.penumbra_transition_sec)) / self.penumbra_transition_sec
            is_sunlight = True
            flux = self.solar_constant_w_m2 * fraction_exit
            incidence_deg = 45.0 * (1.0 - fraction_exit)
        elif t_in_orbit > (self.orbit_period_sec - self.penumbra_transition_sec):
            # Penumbra entry transition
            fraction_entry = (self.orbit_period_sec - t_in_orbit) / self.penumbra_transition_sec
            is_sunlight = True
            flux = self.solar_constant_w_m2 * fraction_entry
            incidence_deg = 45.0 * (1.0 - fraction_entry)
        else:
            # Full Sunlight
            is_sunlight = True
            # Solar panel tracking approximation (varying incidence angle with small cosine variation)
            sunlight_time = t_in_orbit - eclipse_duration
            sunlight_duration = self.orbit_period_sec - eclipse_duration
            phase = (sunlight_time / sunlight_duration) * math.pi
            # Sun incidence angle relative to array normal (0 = normal, optimal)
            incidence_deg = 15.0 * math.sin(phase)
            cos_factor = max(0.0, math.cos(math.radians(incidence_deg)))
            flux = self.solar_constant_w_m2 * cos_factor

        return OrbitState(
            time_sec=time_sec,
            orbit_fraction=orbit_fraction,
            is_sunlight=is_sunlight,
            solar_flux_w_m2=flux,
            sun_incidence_angle_deg=incidence_deg
        )
