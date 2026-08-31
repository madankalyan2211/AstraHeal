"""Communication-aware autonomy manager and arbitration decision engine."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.communication.channel import CommunicationChannel, CommunicationState, LinkStatus
from src.diagnosis.schema import DiagnosisReport
from src.planner.recovery_planner import ActionPlanReport
from src.planner.scenario import ScenarioResult


class AutonomyActionType(str, Enum):
    """Arbitrated autonomy decision."""
    ACT_AUTONOMOUSLY = "ACT_AUTONOMOUSLY"
    WAIT_FOR_GROUND = "WAIT_FOR_GROUND"


class AutonomyArbitrationDecision(BaseModel):
    """Auditable arbitration result deciding between onboard execution and ground handoff."""
    timestamp: float
    decision: AutonomyActionType
    time_to_criticality_sec: float
    time_to_ground_contact_sec: float
    ground_decision_latency_budget_sec: float
    safety_margin_sec: float
    link_status: LinkStatus
    rationale: str
    recommended_plan: Optional[ActionPlanReport]


class CommunicationAwareAutonomyManager:
    """Arbitrates between autonomous onboard recovery and deferring to Earth ground control.
    
    Decision Principle:
    - If unmitigated time-to-criticality (T_crit) is LESS THAN time-to-ground-intervention (T_contact + T_ground_ops):
      -> Spacecraft MUST ACT AUTONOMOUSLY to avert irreversible loss.
    - If T_crit allows ample time for ground operators to review high-rate telemetry and upload vetted commands:
      -> Spacecraft DEFERS TO GROUND (WAIT_FOR_GROUND), buffering fault diagnostics and downlinking at next pass.
    """

    def __init__(
        self,
        channel: Optional[CommunicationChannel] = None,
        ground_operator_decision_latency_sec: float = 300.0,  # 5 min operator assessment allowance
        safety_time_margin_factor: float = 1.5
    ):
        self.channel = channel or CommunicationChannel()
        self.ground_ops_latency = ground_operator_decision_latency_sec
        self.safety_margin = safety_time_margin_factor

    def estimate_time_to_criticality(
        self,
        noop_scenario: Optional[ScenarioResult],
        diagnosis: DiagnosisReport
    ) -> float:
        """Estimate time in seconds until the unmitigated fault breaches hard physical barriers."""
        if noop_scenario is None or noop_scenario.survived:
            # If no-op survives the full horizon, urgency is low
            return 7200.0  # 2 hours+

        # Check trajectory for earliest hard threshold breach
        traj = noop_scenario.risk_metrics
        if traj.thermal_runaway_triggered or traj.voltage_collapse_triggered:
            # Urgent fault: estimated from horizon fraction or fast onset
            return 300.0  # 5 minutes
        
        return 900.0  # 15 minutes default critical window

    def arbitrate(
        self,
        current_time_sec: float,
        diagnosis: DiagnosisReport,
        plan: ActionPlanReport,
        noop_scenario: Optional[ScenarioResult] = None
    ) -> AutonomyArbitrationDecision:
        """Evaluate communication state vs fault urgency to select autonomous action or ground deferral."""
        comm_state = self.channel.evaluate_state(current_time_sec)
        
        t_crit = self.estimate_time_to_criticality(noop_scenario, diagnosis)
        t_contact = comm_state.time_to_next_contact_sec
        total_ground_intervention_time = t_contact + self.ground_ops_latency + comm_state.one_way_latency_sec * 2

        # Required margin
        required_time_with_margin = total_ground_intervention_time * self.safety_margin

        if comm_state.link_status == LinkStatus.IN_CONTACT:
            # Ground link is currently active!
            if t_crit < (self.ground_ops_latency * 0.5):
                # Immediate runaway imminent in < 2.5 min: onboard system must safe immediately
                decision = AutonomyActionType.ACT_AUTONOMOUSLY
                rationale = (
                    f"Real-time link is active, but critical failure onset ({t_crit:.0f}s) is faster than ground operator reaction budget ({self.ground_ops_latency:.0f}s). Immediate autonomous mitigation authorized."
                )
            else:
                decision = AutonomyActionType.WAIT_FOR_GROUND
                rationale = (
                    f"Direct ground link active with {comm_state.active_station} ({comm_state.current_pass_remaining_sec:.0f}s remaining). Telemetry downlinked for human verification."
                )
        else:
            # Spacecraft is in communication blackout / out of ground range
            if t_crit <= required_time_with_margin:
                decision = AutonomyActionType.ACT_AUTONOMOUSLY
                rationale = (
                    f"Next ground contact is in {t_contact:.0f}s (total ground delay {total_ground_intervention_time:.0f}s), which exceeds critical failure threshold ({t_crit:.0f}s with {self.safety_margin}x safety margin). Onboard autonomous action MANDATORY."
                )
            else:
                decision = AutonomyActionType.WAIT_FOR_GROUND
                rationale = (
                    f"Fault severity is non-critical (time-to-criticality {t_crit:.0f}s). Ground contact in {t_contact:.0f}s allows safe operator review. Telemetry queued for downlink."
                )

        return AutonomyArbitrationDecision(
            timestamp=current_time_sec,
            decision=decision,
            time_to_criticality_sec=t_crit,
            time_to_ground_contact_sec=t_contact,
            ground_decision_latency_budget_sec=self.ground_ops_latency,
            safety_margin_sec=required_time_with_margin,
            link_status=comm_state.link_status,
            rationale=rationale,
            recommended_plan=plan if decision == AutonomyActionType.ACT_AUTONOMOUSLY else None
        )
