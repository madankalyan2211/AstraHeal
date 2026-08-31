"""Unit tests for Stage 9 Communication-Aware Autonomy."""

import pytest
from src.communication.channel import CommunicationChannel, LinkStatus, GroundStationPass
from src.communication.manager import CommunicationAwareAutonomyManager, AutonomyActionType
from src.diagnosis.schema import DiagnosisReport, DiagnosisStatus, FailureMode
from src.planner.recovery_planner import ActionPlanReport
from src.planner.actions import RecoveryAction, RecoveryActionType
from src.planner.scenario import ScenarioResult, RiskMetrics, MissionImpact


@pytest.fixture
def comm_manager():
    channel = CommunicationChannel(orbit_period_sec=5740.0, pass_duration_sec=600.0)
    return CommunicationAwareAutonomyManager(channel=channel)


def test_ground_pass_schedule():
    """Verify ground pass detection and time-to-contact calculation."""
    channel = CommunicationChannel(orbit_period_sec=5740.0, pass_duration_sec=600.0)
    
    # At t=0 (orbit start), out of range, next pass around t=2296s
    state_init = channel.evaluate_state(0.0)
    assert state_init.link_status == LinkStatus.OUT_OF_RANGE
    assert state_init.time_to_next_contact_sec > 2000.0

    # At t=2400s (inside pass window)
    state_pass = channel.evaluate_state(2400.0)
    assert state_pass.link_status == LinkStatus.IN_CONTACT
    assert state_pass.active_station is not None
    assert state_pass.current_pass_remaining_sec > 0.0


def test_critical_fault_during_blackout_acts_autonomously(comm_manager):
    """Verify system acts autonomously when critical fault strikes during communication blackout."""
    # Fast critical failure (time-to-criticality = 300s) while ground contact is 2200s away
    crit_scenario = ScenarioResult(
        action=RecoveryAction(action_id="NOOP", action_type=RecoveryActionType.CONTINUE_NOMINAL, description=""),
        simulation_seed=42,
        duration_sec=3000.0,
        survived=False,  # Fails!
        risk_metrics=RiskMetrics(
            max_battery_temp_c=58.0,
            min_bus_voltage_v=24.0,
            max_battery_current_a=15.0,
            min_state_of_charge=0.8,
            final_state_of_charge=0.8,
            cumulative_joule_heat_kj=100.0,
            thermal_runaway_triggered=True
        ),
        mission_impact=MissionImpact(
            payload_availability_fraction=1.0,
            energy_margin_wh=500.0,
            battery_degradation_delta_soh=0.001,
            reversibility_score=1.0,
            disruption_penalty=0.0
        )
    )

    diag = DiagnosisReport(
        timestamp=100.0,
        status=DiagnosisStatus.KNOWN_FAILURE,
        primary_failure_mode=FailureMode.THERMAL_RUNAWAY_INITIATION.value,
        affected_subsystem="EPS_THERMAL",
        confidence=0.95,
        uncertainty=0.05,
        epistemic_uncertainty=0.02,
        aleatoric_uncertainty=0.03,
        method="Bayesian"
    )

    plan = ActionPlanReport(
        timestamp=100.0,
        diagnosis="THERMAL_RUNAWAY",
        confidence=0.95,
        total_candidates_evaluated=3,
        approved_candidates_count=2,
        rejected_candidates_count=1,
        selected_action=RecoveryAction(action_id="ACT-01", action_type=RecoveryActionType.ENTER_SAFE_MODE, description=""),
        selection_score=0.85
    )

    arbitration = comm_manager.arbitrate(
        current_time_sec=100.0,  # Blackout phase
        diagnosis=diag,
        plan=plan,
        noop_scenario=crit_scenario
    )

    assert arbitration.decision == AutonomyActionType.ACT_AUTONOMOUSLY
    assert arbitration.recommended_plan is not None
    assert "MANDATORY" in arbitration.rationale or "autonomous" in arbitration.rationale.lower()


def test_non_critical_fault_defers_to_ground(comm_manager):
    """Verify system defers to ground when time to failure allows safe ground review."""
    # Benign slow fault with 2 hours until threshold
    benign_scenario = ScenarioResult(
        action=RecoveryAction(action_id="NOOP", action_type=RecoveryActionType.CONTINUE_NOMINAL, description=""),
        simulation_seed=42,
        duration_sec=3000.0,
        survived=True,  # Spacecraft survives easily
        risk_metrics=RiskMetrics(
            max_battery_temp_c=25.0,
            min_bus_voltage_v=27.5,
            max_battery_current_a=5.0,
            min_state_of_charge=0.90,
            final_state_of_charge=0.92,
            cumulative_joule_heat_kj=20.0
        ),
        mission_impact=MissionImpact(
            payload_availability_fraction=1.0,
            energy_margin_wh=800.0,
            battery_degradation_delta_soh=0.0001,
            reversibility_score=1.0,
            disruption_penalty=0.0
        )
    )

    diag = DiagnosisReport(
        timestamp=100.0,
        status=DiagnosisStatus.KNOWN_FAILURE,
        primary_failure_mode=FailureMode.SENSOR_BIAS_DRIFT.value,
        affected_subsystem="EPS_INSTRUMENTATION",
        confidence=0.80,
        uncertainty=0.20,
        epistemic_uncertainty=0.05,
        aleatoric_uncertainty=0.15,
        method="Bayesian"
    )

    plan = ActionPlanReport(
        timestamp=100.0,
        diagnosis="SENSOR_BIAS_DRIFT",
        confidence=0.80,
        total_candidates_evaluated=3,
        approved_candidates_count=3,
        rejected_candidates_count=0,
        selected_action=None,
        selection_score=0.90
    )

    arbitration = comm_manager.arbitrate(
        current_time_sec=100.0,
        diagnosis=diag,
        plan=plan,
        noop_scenario=benign_scenario
    )

    assert arbitration.decision == AutonomyActionType.WAIT_FOR_GROUND
    assert arbitration.recommended_plan is None
    assert "safe operator review" in arbitration.rationale.lower() or "queued" in arbitration.rationale.lower()
