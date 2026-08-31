"""Ground station pass modeling, link availability, and transmission latency."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LinkStatus(str, Enum):
    """Real-time RF link state."""
    IN_CONTACT = "IN_CONTACT"
    BLACKOUT_OCCULTATION = "BLACKOUT_OCCULTATION"
    OUT_OF_RANGE = "OUT_OF_RANGE"


class GroundStationPass(BaseModel):
    """Scheduled ground station visibility window."""
    station_name: str
    pass_start_sec: float
    pass_end_sec: float
    bandwidth_kbps: float = 256.0
    uplink_latency_sec: float = 2.0  # One-way propagation + processing delay

    def is_in_window(self, current_time_sec: float) -> bool:
        return self.pass_start_sec <= current_time_sec <= self.pass_end_sec


class CommunicationState(BaseModel):
    """Instantaneous communication environment state."""
    current_time_sec: float
    link_status: LinkStatus
    active_station: Optional[str]
    time_to_next_contact_sec: float
    current_pass_remaining_sec: float
    one_way_latency_sec: float
    available_bandwidth_kbps: float


class CommunicationChannel:
    """Simulates realistic orbital ground network visibility, latency, and telemetry/command buffering."""

    def __init__(
        self,
        orbit_period_sec: float = 5740.0,
        pass_duration_sec: float = 600.0,    # 10 minute pass per orbit
        default_latency_sec: float = 2.5,
        default_bandwidth_kbps: float = 512.0
    ):
        self.orbit_period = orbit_period_sec
        self.pass_duration = pass_duration_sec
        self.default_latency = default_latency_sec
        self.default_bandwidth = default_bandwidth_kbps
        self.passes: List[GroundStationPass] = []
        self._generate_default_passes(num_orbits=10)

    def _generate_default_passes(self, num_orbits: int = 10) -> None:
        """Generate periodic ground passes over Svalbard / White Sands ground stations."""
        stations = ["SVALBARD-GS", "WHITE-SANDS-GS", "WALLOPS-GS"]
        for orb in range(num_orbits):
            t_pass_start = orb * self.orbit_period + (self.orbit_period * 0.40)
            t_pass_end = t_pass_start + self.pass_duration
            self.passes.append(GroundStationPass(
                station_name=stations[orb % len(stations)],
                pass_start_sec=t_pass_start,
                pass_end_sec=t_pass_end,
                bandwidth_kbps=self.default_bandwidth,
                uplink_latency_sec=self.default_latency
            ))

    def evaluate_state(self, current_time_sec: float) -> CommunicationState:
        """Compute active link availability, time to next pass, and channel parameters."""
        active_pass = None
        for p in self.passes:
            if p.is_in_window(current_time_sec):
                active_pass = p
                break

        if active_pass:
            return CommunicationState(
                current_time_sec=current_time_sec,
                link_status=LinkStatus.IN_CONTACT,
                active_station=active_pass.station_name,
                time_to_next_contact_sec=0.0,
                current_pass_remaining_sec=float(active_pass.pass_end_sec - current_time_sec),
                one_way_latency_sec=active_pass.uplink_latency_sec,
                available_bandwidth_kbps=active_pass.bandwidth_kbps
            )

        # Find time to next upcoming pass
        future_passes = [p for p in self.passes if p.pass_start_sec > current_time_sec]
        if future_passes:
            next_pass = min(future_passes, key=lambda x: x.pass_start_sec)
            time_to_next = float(next_pass.pass_start_sec - current_time_sec)
            station = next_pass.station_name
        else:
            time_to_next = 3600.0  # Fallback 1 hour
            station = None

        return CommunicationState(
            current_time_sec=current_time_sec,
            link_status=LinkStatus.OUT_OF_RANGE,
            active_station=None,
            time_to_next_contact_sec=time_to_next,
            current_pass_remaining_sec=0.0,
            one_way_latency_sec=self.default_latency,
            available_bandwidth_kbps=0.0
        )
