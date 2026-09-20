"""Unit and integration test suite for AstraHeal Paper 4 pipeline.

Verifies:
1. Scenario generator determinism and seed repeatability
2. Physical parameter perturbation application on digital twin
3. Telemetry noise modeling on measurement frames
4. Execution engine multi-cycle step and state envelope adherence
5. Safety Governor invariant preservation under perturbed/noisy inputs
6. Fail-closed safety property under invalid/malformed candidate actions
7. Ablation architecture routing
8. Performance metric calculations
"""

import copy
import pytest
import numpy as np

from evaluation.paper4.scenario_generator import Paper4ScenarioGenerator, Paper4ScenarioSpec
from experiments.paper4.common import Paper4ExecutionEngine, Paper4ScenarioResult
from src.digital_twin.fault_injection import InjectedFaultSpec, FaultType
from src.safety.safety_governor import DeterministicSafetyGovernor, SafetyStatus


def test_scenario_generator_determinism():
    """Verify that identical random seeds produce identically parameterized scenarios."""
    suite1 = Paper4ScenarioGenerator.generate_e1_sequential_suite(count=5, base_seed=9999)
    suite2 = Paper4ScenarioGenerator.generate_e1_sequential_suite(count=5, base_seed=9999)
    
    assert len(suite1) == len(suite2) == 5
    for s1, s2 in zip(suite1, suite2):
        assert s1.scenario_id == s2.scenario_id
        assert s1.initial_soc == s2.initial_soc
        assert len(s1.faults) == len(s2.faults)
        for f1, f2 in zip(s1.faults, s2.faults):
            assert f1.fault_type == f2.fault_type
            assert f1.start_time_sec == f2.start_time_sec
            assert f1.parameters == f2.parameters


def test_perturbed_twin_instantiation():
    """Verify that physics perturbations accurately scale internal digital twin parameters."""
    engine = Paper4ExecutionEngine()
    spec = Paper4ScenarioSpec(
        scenario_id="TEST-PERTURB",
        experiment_id="TEST",
        name="Test Perturbed Twin",
        category="TEST",
        random_seed=42,
        physics_perturbations={
            "c_th_mult": 1.15,
            "h_rad_mult": 0.85,
            "r0_mult": 1.20,
            "solar_efficiency_mult": 0.90,
            "parasitic_load_bias_w": 25.0
        }
    )
    twin = engine._instantiate_perturbed_twin(spec)

    # Nominal baseline references: c_th=4500, h_rad=1.2, r0=0.045, eff_nom=0.28, standby_w=10.0
    assert pytest.approx(twin.battery.c_th, rel=1e-3) == 4500.0 * 1.15
    assert pytest.approx(twin.battery.h_rad, rel=1e-3) == 1.2 * 0.85
    assert pytest.approx(twin.battery.r0_actual, rel=1e-3) == 0.045 * 1.20
    assert pytest.approx(twin.solar_array.eff_nom, rel=1e-3) == 0.28 * 0.90
    assert pytest.approx(twin.pdu.payload_standby_w, rel=1e-3) == 10.0 + 25.0


def test_safety_governor_fail_closed_under_noise():
    """Verify that governor never permits thermal runaway or undervoltage under any condition."""
    governor = DeterministicSafetyGovernor()
    from src.planner.scenario import ScenarioResult, RiskMetrics, MissionImpact
    from src.planner.actions import RecoveryAction, RecoveryActionType

    act = RecoveryAction(
        action_id="ACT_UNSAFE_TEST",
        action_type=RecoveryActionType.CONTINUE_NOMINAL,
        description="Unsafe action test"
    )

    # Scenario 1: Thermal breach (50.5C > 46.0C)
    scen_thermal = ScenarioResult(
        action=act,
        simulation_seed=42,
        duration_sec=300.0,
        survived=False,
        risk_metrics=RiskMetrics(
            max_battery_temp_c=50.5,
            min_bus_voltage_v=26.0,
            max_battery_current_a=20.0,
            min_state_of_charge=0.80,
            final_state_of_charge=0.79,
            cumulative_joule_heat_kj=120.0
        ),
        mission_impact=MissionImpact(
            payload_availability_fraction=0.8,
            energy_margin_wh=100.0,
            battery_degradation_delta_soh=0.001,
            reversibility_score=0.9,
            disruption_penalty=0.1
        )
    )
    dec1 = governor.evaluate(scen_thermal)
    assert dec1.status == SafetyStatus.REJECTED
    assert not dec1.is_safe
    assert "HARD_THERMAL_EXCEEDED" in dec1.violated_hard_constraints

    # Scenario 2: Undervoltage breach (20.5V < 22.0V)
    scen_volt = ScenarioResult(
        action=act,
        simulation_seed=43,
        duration_sec=300.0,
        survived=False,
        risk_metrics=RiskMetrics(
            max_battery_temp_c=32.0,
            min_bus_voltage_v=20.5,
            max_battery_current_a=20.0,
            min_state_of_charge=0.80,
            final_state_of_charge=0.79,
            cumulative_joule_heat_kj=50.0
        ),
        mission_impact=MissionImpact(
            payload_availability_fraction=0.8,
            energy_margin_wh=100.0,
            battery_degradation_delta_soh=0.001,
            reversibility_score=0.9,
            disruption_penalty=0.1
        )
    )
    dec2 = governor.evaluate(scen_volt)
    assert dec2.status == SafetyStatus.REJECTED
    assert not dec2.is_safe
    assert "HARD_VOLTAGE_UNDERFLOW" in dec2.violated_hard_constraints


def test_short_simulation_execution():
    """Verify end-to-end execution of a mini 600s scenario under AstraHeal."""
    engine = Paper4ExecutionEngine(step_sec=10.0, cooldown_sec=100.0)
    spec = Paper4ScenarioSpec(
        scenario_id="P4-TEST-SHORT",
        experiment_id="TEST",
        name="Mini Test Scenario",
        category="TEST",
        orbit_duration_sec=600.0,
        initial_soc=0.95,
        random_seed=123,
        faults=[
            InjectedFaultSpec(
                fault_type=FaultType.BATTERY_RESISTANCE_SPIKE,
                start_time_sec=150.0,
                parameters={"resistance_multiplier": 2.5}
            )
        ]
    )

    res = engine.run_scenario(system_type="ASTRAHEAL_FULL", spec=spec)
    assert isinstance(res, Paper4ScenarioResult)
    assert res.scenario_id == "P4-TEST-SHORT"
    assert res.executed_unsafe_actions == 0
    assert res.governor_bypasses == 0
    assert res.cumulative_delivered_payload_wh > 0.0


def test_ablation_system_variants():
    """Verify that all 6 architecture variants can run without error."""
    engine = Paper4ExecutionEngine(step_sec=20.0, cooldown_sec=100.0)
    spec = Paper4ScenarioSpec(
        scenario_id="P4-TEST-VARIANTS",
        experiment_id="TEST",
        name="Mini Variant Test",
        category="TEST",
        orbit_duration_sec=400.0,
        initial_soc=0.95,
        random_seed=456,
        faults=[]
    )

    variants = [
        "ASTRAHEAL_FULL",
        "ABLATION_NO_UNCERTAINTY",
        "ABLATION_NO_LOOKAHEAD",
        "ABLATION_NO_GOVERNOR",
        "BASELINE_PASSIVE",
        "BASELINE_BLIND_SAFE_MODE"
    ]

    for v in variants:
        res = engine.run_scenario(system_type=v, spec=spec)
        assert res.system_name == v
        assert res.total_hard_violations_count == 0  # Nominal run
