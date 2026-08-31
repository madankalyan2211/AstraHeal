"""Unit tests for Stage 8 Autonomous Recovery Planner."""

import pytest
from src.digital_twin.simulator import SpacecraftEPSDigitalTwin
from src.digital_twin.fault_injection import InjectedFaultSpec, FaultType
from src.diagnosis.schema import DiagnosisReport, DiagnosisStatus, FailureMode
from src.planner.recovery_planner import AutonomousRecoveryPlanner, ActionPlanReport
from src.planner.actions import RecoveryActionType


def test_planner_end_to_end_decision():
    """Verify autonomous planner simulates branches, gates via governor, and chooses optimal safe action."""
    twin = SpacecraftEPSDigitalTwin(random_seed=42)
    # Inject severe thermal runaway anomaly
    twin.inject_fault(InjectedFaultSpec(
        fault_type=FaultType.THERMAL_RUNAWAY,
        start_time_sec=0.0,
        parameters={"exothermic_heat_w": 140.0}
    ))
    twin.step(dt_sec=100.0)

    diag = DiagnosisReport(
        timestamp=100.0,
        status=DiagnosisStatus.KNOWN_FAILURE,
        primary_failure_mode=FailureMode.THERMAL_RUNAWAY_INITIATION.value,
        affected_subsystem="EPS_THERMAL",
        confidence=0.96,
        uncertainty=0.04,
        epistemic_uncertainty=0.02,
        aleatoric_uncertainty=0.03,
        method="Bayesian"
    )

    planner = AutonomousRecoveryPlanner()
    plan = planner.plan_recovery(twin, diag, horizon_sec=2000.0)

    assert plan.total_candidates_evaluated >= 3
    assert plan.selected_action is not None
    assert plan.selection_score > -1e5
    assert len(plan.decision_rationale) > 0

    # Ensure No-Op (continuing nominal with heating) is rejected or ranked lower than mitigation
    noop_eval = next((s for s in plan.all_evaluated_scenarios if s["action_type"] == RecoveryActionType.CONTINUE_NOMINAL.value), None)
    if noop_eval:
        assert noop_eval["safety_status"] == "REJECTED" or noop_eval["score"] < plan.selection_score


def test_plan_execution_on_digital_twin():
    """Verify applying the approved plan mutates the active digital twin into the recovered state."""
    twin = SpacecraftEPSDigitalTwin(random_seed=42)
    planner = AutonomousRecoveryPlanner()
    
    diag = DiagnosisReport(
        timestamp=50.0,
        status=DiagnosisStatus.KNOWN_FAILURE,
        primary_failure_mode=FailureMode.BATTERY_INTERNAL_RESISTANCE_SPIKE.value,
        affected_subsystem="EPS_BATTERY",
        confidence=0.90,
        uncertainty=0.10,
        epistemic_uncertainty=0.03,
        aleatoric_uncertainty=0.05,
        method="Bayesian"
    )

    plan = planner.plan_recovery(twin, diag, horizon_sec=1000.0)
    success = planner.execute_plan_on_twin(twin, plan)
    assert success is True
