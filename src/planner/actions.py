"""Candidate recovery action definitions and domain-specific action generators."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.diagnosis.schema import DiagnosisReport, FailureMode
from src.digital_twin.power_distribution import SpacecraftOperatingMode


class RecoveryActionType(str, Enum):
    """Catalog of physically and operationally valid spacecraft EPS recovery actions."""
    CONTINUE_NOMINAL = "CONTINUE_NOMINAL"
    REDUCE_PAYLOAD_LOAD = "REDUCE_PAYLOAD_LOAD"
    DISABLE_NON_CRITICAL_SUBSYSTEM = "DISABLE_NON_CRITICAL_SUBSYSTEM"
    REDUCE_HEATER_POWER = "REDUCE_HEATER_POWER"
    ENTER_SAFE_MODE = "ENTER_SAFE_MODE"
    REDISTRIBUTE_POWER = "REDISTRIBUTE_POWER"
    DEFER_NON_CRITICAL_ACTIVITY = "DEFER_NON_CRITICAL_ACTIVITY"


class RecoveryAction(BaseModel):
    """Specification of a candidate recovery action for counterfactual evaluation."""
    action_id: str
    action_type: RecoveryActionType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    description: str
    is_reversible: bool = True
    estimated_implementation_cost: float = Field(default=0.0, description="Normalized cost or disruption [0.0, 1.0]")

    def apply_to_digital_twin(self, twin: Any) -> None:
        """Execute physical reconfiguration on digital twin instance."""
        if self.action_type == RecoveryActionType.CONTINUE_NOMINAL:
            pass  # No-op baseline

        elif self.action_type == RecoveryActionType.ENTER_SAFE_MODE:
            twin.pdu.set_mode(SpacecraftOperatingMode.SAFE_MODE)

        elif self.action_type == RecoveryActionType.REDUCE_PAYLOAD_LOAD:
            throttle_fraction = self.parameters.get("throttle_fraction", 0.50)
            twin.pdu.payload_active_w *= (1.0 - throttle_fraction)
            twin.pdu.payload_standby_w *= (1.0 - throttle_fraction)

        elif self.action_type == RecoveryActionType.DISABLE_NON_CRITICAL_SUBSYSTEM:
            target = self.parameters.get("subsystem", "PAYLOAD")
            if target == "PAYLOAD":
                twin.pdu.payload_active_w = 0.0
                twin.pdu.payload_standby_w = 0.0
            elif target == "HEATERS":
                twin.pdu.heaters_w = 0.0

        elif self.action_type == RecoveryActionType.REDUCE_HEATER_POWER:
            reduction = self.parameters.get("reduction_fraction", 0.50)
            twin.pdu.heaters_w *= (1.0 - reduction)

        elif self.action_type == RecoveryActionType.REDISTRIBUTE_POWER:
            # Drop transmitter to receive-only to save 65W
            twin.pdu.ttc_tx_w = twin.pdu.ttc_rx_w
            if twin.pdu.current_mode == SpacecraftOperatingMode.TRANSMISSION:
                twin.pdu.set_mode(SpacecraftOperatingMode.STANDBY)

        elif self.action_type == RecoveryActionType.DEFER_NON_CRITICAL_ACTIVITY:
            if twin.pdu.current_mode == SpacecraftOperatingMode.SCIENCE:
                twin.pdu.set_mode(SpacecraftOperatingMode.STANDBY)


class ActionGenerator:
    """Generates physically meaningful candidate recovery actions based on diagnosis and mission state."""

    @staticmethod
    def generate_candidates(diagnosis: DiagnosisReport, current_twin: Any) -> List[RecoveryAction]:
        """Generate a diverse set of candidate actions tailored to the diagnosed failure mode."""
        candidates = []

        # 1. Baseline no-op action is ALWAYS included to evaluate unmitigated risk
        candidates.append(RecoveryAction(
            action_id="ACT-00-NOOP",
            action_type=RecoveryActionType.CONTINUE_NOMINAL,
            description="Continue nominal operations without intervention (Baseline No-Op)",
            is_reversible=True,
            estimated_implementation_cost=0.0
        ))

        # 2. General Safe Mode is always an emergency candidate
        candidates.append(RecoveryAction(
            action_id="ACT-01-SAFE-MODE",
            action_type=RecoveryActionType.ENTER_SAFE_MODE,
            description="Transition spacecraft to minimal power Safe Mode (OBC + basic TT&C)",
            is_reversible=True,
            estimated_implementation_cost=0.85
        ))

        # 3. Fault-tailored candidate actions
        mode = diagnosis.primary_failure_mode

        if mode == FailureMode.BATTERY_INTERNAL_RESISTANCE_SPIKE.value:
            candidates.extend([
                RecoveryAction(
                    action_id="ACT-02-THROTTLE-PAYLOAD-50",
                    action_type=RecoveryActionType.REDUCE_PAYLOAD_LOAD,
                    parameters={"throttle_fraction": 0.50},
                    description="Throttle science payload power draw by 50% to reduce Joule heating (I^2*R)",
                    is_reversible=True,
                    estimated_implementation_cost=0.40
                ),
                RecoveryAction(
                    action_id="ACT-03-DISABLE-PAYLOAD",
                    action_type=RecoveryActionType.DISABLE_NON_CRITICAL_SUBSYSTEM,
                    parameters={"subsystem": "PAYLOAD"},
                    description="Completely disable science payload to minimize battery discharge current",
                    is_reversible=True,
                    estimated_implementation_cost=0.60
                ),
                RecoveryAction(
                    action_id="ACT-04-DEFER-SCIENCE",
                    action_type=RecoveryActionType.DEFER_NON_CRITICAL_ACTIVITY,
                    description="Defer active science observation to sunlight charging phases only",
                    is_reversible=True,
                    estimated_implementation_cost=0.30
                )
            ])

        elif mode == FailureMode.THERMAL_RUNAWAY_INITIATION.value:
            candidates.extend([
                RecoveryAction(
                    action_id="ACT-02-CUT-HEATERS",
                    action_type=RecoveryActionType.DISABLE_NON_CRITICAL_SUBSYSTEM,
                    parameters={"subsystem": "HEATERS"},
                    description="Immediately disable all non-essential thermal heaters",
                    is_reversible=True,
                    estimated_implementation_cost=0.20
                ),
                RecoveryAction(
                    action_id="ACT-03-SHUTDOWN-PAYLOAD",
                    action_type=RecoveryActionType.DISABLE_NON_CRITICAL_SUBSYSTEM,
                    parameters={"subsystem": "PAYLOAD"},
                    description="Shutdown high-power payload electronics to reduce internal heat generation",
                    is_reversible=True,
                    estimated_implementation_cost=0.60
                )
            ])

        elif mode == FailureMode.SOLAR_ARRAY_STRING_FAULT.value:
            candidates.extend([
                RecoveryAction(
                    action_id="ACT-02-THROTTLE-PAYLOAD-40",
                    action_type=RecoveryActionType.REDUCE_PAYLOAD_LOAD,
                    parameters={"throttle_fraction": 0.40},
                    description="Throttle payload demand to balance reduced solar array generation capacity",
                    is_reversible=True,
                    estimated_implementation_cost=0.35
                ),
                RecoveryAction(
                    action_id="ACT-03-DEFER-TX",
                    action_type=RecoveryActionType.REDISTRIBUTE_POWER,
                    description="Inhibit high-power RF transmission and buffer telemetry",
                    is_reversible=True,
                    estimated_implementation_cost=0.25
                )
            ])

        elif mode == FailureMode.PARASITIC_BUS_OVERLOAD.value:
            candidates.extend([
                RecoveryAction(
                    action_id="ACT-02-SHED-PAYLOAD",
                    action_type=RecoveryActionType.DISABLE_NON_CRITICAL_SUBSYSTEM,
                    parameters={"subsystem": "PAYLOAD"},
                    description="Isolate payload bus line to arrest parasitic current draw",
                    is_reversible=True,
                    estimated_implementation_cost=0.55
                ),
                RecoveryAction(
                    action_id="ACT-03-REDISTRIBUTE-BUS",
                    action_type=RecoveryActionType.REDISTRIBUTE_POWER,
                    description="Redistribute bus lines and shut down non-essential transmitters",
                    is_reversible=True,
                    estimated_implementation_cost=0.30
                )
            ])

        else:
            # Generic / Unknown anomaly candidates
            candidates.extend([
                RecoveryAction(
                    action_id="ACT-02-THROTTLE-PAYLOAD-50",
                    action_type=RecoveryActionType.REDUCE_PAYLOAD_LOAD,
                    parameters={"throttle_fraction": 0.50},
                    description="Throttle science payload by 50% to reduce bus power load and Joule heating",
                    is_reversible=True,
                    estimated_implementation_cost=0.40
                ),
                RecoveryAction(
                    action_id="ACT-03-DISABLE-PAYLOAD",
                    action_type=RecoveryActionType.DISABLE_NON_CRITICAL_SUBSYSTEM,
                    parameters={"subsystem": "PAYLOAD"},
                    description="Isolate science payload completely to protect battery health and preserve bus stability",
                    is_reversible=True,
                    estimated_implementation_cost=0.60
                ),
                RecoveryAction(
                    action_id="ACT-04-CONSERVATIVE-STANDBY",
                    action_type=RecoveryActionType.DEFER_NON_CRITICAL_ACTIVITY,
                    description="Drop to conservative standby mode while gathering evidence",
                    is_reversible=True,
                    estimated_implementation_cost=0.30
                )
            ])

        return candidates
