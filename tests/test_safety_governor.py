"""Unit tests for Stage 8 Deterministic Safety Governor."""

import pytest
from src.planner.actions import RecoveryAction, RecoveryActionType
from src.planner.scenario import ScenarioResult, RiskMetrics, MissionImpact
from src.safety.safety_governor import DeterministicSafetyGovernor, SafetyStatus


@pytest.fixture
def governor():
    return DeterministicSafetyGovernor()


def test_safety_governor_approves_safe_scenario(governor):
    """Verify governor approves scenario within all hard thermal and electrical limits."""
    scen = ScenarioResult(
        action=RecoveryAction(
            action_id="ACT-SAFE",
            action_type=RecoveryActionType.REDUCE_PAYLOAD_LOAD,
            description="Safe action"
        ),
        simulation_seed=42,
        duration_sec=3000.0,
        survived=True,
        risk_metrics=RiskMetrics(
            max_battery_temp_c=32.5,     # Well below 46°C limit
            min_bus_voltage_v=26.4,      # Well above 22V limit
            max_battery_current_a=12.0,  # Below 40A limit
            min_state_of_charge=0.75,    # Above 15% floor
            final_state_of_charge=0.82,
            cumulative_joule_heat_kj=45.0
        ),
        mission_impact=MissionImpact(
            payload_availability_fraction=0.60,
            energy_margin_wh=600.0,
            battery_degradation_delta_soh=0.0001,
            reversibility_score=1.0,
            disruption_penalty=0.40
        )
    )

    decision = governor.evaluate(scen)
    assert decision.status == SafetyStatus.APPROVED
    assert decision.is_safe is True
    assert len(decision.violated_hard_constraints) == 0
    assert decision.safety_margins["thermal_margin_c"] > 10.0


def test_safety_governor_rejects_thermal_breach(governor):
    """Verify governor rejects scenario where temperature exceeds hard safety limit."""
    scen = ScenarioResult(
        action=RecoveryAction(
            action_id="ACT-UNSAFE-TEMP",
            action_type=RecoveryActionType.CONTINUE_NOMINAL,
            description="Unsafe thermal action"
        ),
        simulation_seed=42,
        duration_sec=3000.0,
        survived=True,
        risk_metrics=RiskMetrics(
            max_battery_temp_c=52.0,     # Exceeds 46°C limit!
            min_bus_voltage_v=26.0,
            max_battery_current_a=15.0,
            min_state_of_charge=0.60,
            final_state_of_charge=0.65,
            cumulative_joule_heat_kj=180.0
        ),
        mission_impact=MissionImpact(
            payload_availability_fraction=1.0,
            energy_margin_wh=500.0,
            battery_degradation_delta_soh=0.001,
            reversibility_score=1.0,
            disruption_penalty=0.0
        )
    )

    decision = governor.evaluate(scen)
    assert decision.status == SafetyStatus.REJECTED
    assert decision.is_safe is False
    assert "HARD_THERMAL_EXCEEDED" in decision.violated_hard_constraints
    assert any("temperature" in r.lower() for r in decision.rejection_reasons)


def test_safety_governor_rejects_undervoltage(governor):
    """Verify governor rejects scenario where bus voltage collapses."""
    scen = ScenarioResult(
        action=RecoveryAction(
            action_id="ACT-UNSAFE-VOLT",
            action_type=RecoveryActionType.CONTINUE_NOMINAL,
            description="Undervoltage action"
        ),
        simulation_seed=42,
        duration_sec=3000.0,
        survived=True,
        risk_metrics=RiskMetrics(
            max_battery_temp_c=25.0,
            min_bus_voltage_v=19.5,      # Collapses below 22.0V limit!
            max_battery_current_a=20.0,
            min_state_of_charge=0.40,
            final_state_of_charge=0.45,
            cumulative_joule_heat_kj=50.0
        ),
        mission_impact=MissionImpact(
            payload_availability_fraction=1.0,
            energy_margin_wh=200.0,
            battery_degradation_delta_soh=0.0005,
            reversibility_score=1.0,
            disruption_penalty=0.0
        )
    )

    decision = governor.evaluate(scen)
    assert decision.status == SafetyStatus.REJECTED
    assert "HARD_VOLTAGE_UNDERFLOW" in decision.violated_hard_constraints
