"""Unit tests for Stage 7 counterfactual mission simulation and branching."""

import pytest
import numpy as np

from src.digital_twin.simulator import SpacecraftEPSDigitalTwin
from src.digital_twin.fault_injection import InjectedFaultSpec, FaultType
from src.diagnosis.schema import DiagnosisReport, DiagnosisStatus, FailureMode
from src.planner.actions import RecoveryAction, RecoveryActionType, ActionGenerator
from src.planner.scenario import ScenarioResult
from src.planner.counterfactual import CounterfactualSimulator


def test_digital_twin_cloning_isolation():
    """Verify that cloning a twin produces a deep independent copy and never mutates original state."""
    twin = SpacecraftEPSDigitalTwin(system_id="BASE-SC", random_seed=42)
    twin.step(dt_sec=100.0)
    
    initial_soc = twin.battery.soc
    initial_time = twin.current_time_sec

    # Clone twin and mutate clone
    clone = twin.clone()
    clone.pdu.payload_active_w = 0.0
    clone.step(dt_sec=500.0)

    # Base twin must remain completely unaffected
    assert twin.current_time_sec == initial_time
    assert twin.battery.soc == initial_soc
    assert twin.pdu.payload_active_w == 120.0  # Nominal default


def test_candidate_action_generation():
    """Verify fault-tailored candidate action generation."""
    diag = DiagnosisReport(
        timestamp=5000.0,
        status=DiagnosisStatus.KNOWN_FAILURE,
        primary_failure_mode=FailureMode.BATTERY_INTERNAL_RESISTANCE_SPIKE.value,
        affected_subsystem="EPS_BATTERY",
        confidence=0.90,
        uncertainty=0.10,
        epistemic_uncertainty=0.05,
        aleatoric_uncertainty=0.08,
        method="Bayesian"
    )
    twin = SpacecraftEPSDigitalTwin()
    candidates = ActionGenerator.generate_candidates(diag, twin)

    assert len(candidates) >= 4
    action_types = [c.action_type for c in candidates]
    assert RecoveryActionType.CONTINUE_NOMINAL in action_types
    assert RecoveryActionType.ENTER_SAFE_MODE in action_types
    assert RecoveryActionType.REDUCE_PAYLOAD_LOAD in action_types


def test_counterfactual_simulation_branching():
    """Verify that counterfactual simulator evaluates all actions and detects difference in outcomes."""
    twin = SpacecraftEPSDigitalTwin(random_seed=42)
    # Inject battery impedance spike
    twin.inject_fault(InjectedFaultSpec(
        fault_type=FaultType.BATTERY_RESISTANCE_SPIKE,
        start_time_sec=0.0,
        parameters={"resistance_multiplier": 4.5}
    ))
    # Step into fault
    twin.step(dt_sec=100.0)

    diag = DiagnosisReport(
        timestamp=100.0,
        status=DiagnosisStatus.KNOWN_FAILURE,
        primary_failure_mode=FailureMode.BATTERY_INTERNAL_RESISTANCE_SPIKE.value,
        affected_subsystem="EPS_BATTERY",
        confidence=0.95,
        uncertainty=0.05,
        epistemic_uncertainty=0.02,
        aleatoric_uncertainty=0.03,
        method="Bayesian"
    )

    candidates = ActionGenerator.generate_candidates(diag, twin)
    sim = CounterfactualSimulator(default_horizon_sec=3000.0, simulation_step_sec=10.0)
    
    results = sim.evaluate_all(twin, candidates)
    assert len(results) == len(candidates)

    # Compare No-Op vs Safe Mode / Throttle
    noop_res = next(r for r in results if r.action.action_type == RecoveryActionType.CONTINUE_NOMINAL)
    safe_res = next(r for r in results if r.action.action_type == RecoveryActionType.ENTER_SAFE_MODE)
    
    # Safe Mode draws less power, preserving higher minimum SoC during eclipse
    assert safe_res.risk_metrics.min_state_of_charge > noop_res.risk_metrics.min_state_of_charge
    assert safe_res.risk_metrics.min_bus_voltage_v >= noop_res.risk_metrics.min_bus_voltage_v


def test_counterfactual_reproducibility():
    """Verify that running counterfactual simulation twice with identical seeds yields identical results."""
    twin = SpacecraftEPSDigitalTwin(random_seed=42)
    twin.step(10.0)
    
    action = RecoveryAction(
        action_id="TEST-ACT",
        action_type=RecoveryActionType.REDUCE_PAYLOAD_LOAD,
        parameters={"throttle_fraction": 0.5},
        description="Test Action"
    )
    sim = CounterfactualSimulator(default_horizon_sec=1000.0)

    res1 = sim.evaluate_action(twin, action)
    res2 = sim.evaluate_action(twin, action)

    assert abs(res1.risk_metrics.final_state_of_charge - res2.risk_metrics.final_state_of_charge) < 1e-6
    assert abs(res1.risk_metrics.max_battery_temp_c - res2.risk_metrics.max_battery_temp_c) < 1e-6
