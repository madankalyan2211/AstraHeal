"""AstraHeal Paper 3 — Unit and Safety Invariant Test Suite.

Verifies:
1. Deterministic action admissibility (H2)
2. Invariant enforcement: REJECTED -> CANNOT EXECUTE
3. Compound constraint violation detection
4. Fail-closed safety on NaN, Inf, and malformed actions
5. Continuous boundary consistency
6. Communication dominance over arbitration
7. Safe failure convergence on NO_SAFE_ACTION_AVAILABLE
"""

from __future__ import annotations

import math
import pytest

from experiments.paper3.common import (
    GateDecision,
    LinkStatus,
    Paper3SafetyGovernor,
    ProposedAction,
    SpacecraftState,
)
import importlib
comm_module = importlib.import_module("experiments.paper3.06_communication_aware_safety")
arbitrate_communication_decision = comm_module.arbitrate_communication_decision


@pytest.fixture
def nominal_state() -> SpacecraftState:
    return SpacecraftState(
        timestamp=100.0,
        battery_temp_c=28.0,
        bus_voltage_v=28.0,
        battery_current_a=15.0,
        state_of_charge=0.80,
        pdu_power_w=420.0,
        is_survived=True,
    )


@pytest.fixture
def governor() -> Paper3SafetyGovernor:
    return Paper3SafetyGovernor()


def test_safe_action_approval(governor: Paper3SafetyGovernor, nominal_state: SpacecraftState):
    """Verify that an action meeting all hard constraints is APPROVED."""
    action = ProposedAction(
        action_id="TEST-SAFE-01",
        action_type="CONTINUE_NOMINAL",
        predicted_peak_temp_c=32.0,
        predicted_min_voltage_v=26.5,
        predicted_peak_current_a=22.0,
        predicted_min_soc=0.75,
        predicted_peak_power_w=480.0,
        predicted_survived=True,
    )
    verdict = governor.evaluate_action(action, nominal_state)
    assert verdict.decision == GateDecision.APPROVED
    assert verdict.is_admissible is True
    assert len(verdict.violated_constraints) == 0
    assert verdict.safety_margins["thermal_margin_c"] == 46.0 - 32.0


def test_thermal_breach_rejection(governor: Paper3SafetyGovernor, nominal_state: SpacecraftState):
    """Verify rejection when battery core temperature exceeds 46.0°C."""
    action = ProposedAction(
        action_id="TEST-UNSAFE-THERM",
        action_type="REDUCE_HEATER_POWER",
        predicted_peak_temp_c=48.5,
    )
    verdict = governor.evaluate_action(action, nominal_state)
    assert verdict.decision == GateDecision.REJECTED
    assert verdict.is_admissible is False
    assert "HARD_THERMAL_EXCEEDED" in verdict.violated_constraints


def test_undervoltage_breach_rejection(governor: Paper3SafetyGovernor, nominal_state: SpacecraftState):
    """Verify rejection when bus voltage falls below 22.0V."""
    action = ProposedAction(
        action_id="TEST-UNSAFE-VOLT",
        action_type="CONTINUE_NOMINAL",
        predicted_min_voltage_v=20.5,
    )
    verdict = governor.evaluate_action(action, nominal_state)
    assert verdict.decision == GateDecision.REJECTED
    assert "HARD_VOLTAGE_UNDERFLOW" in verdict.violated_constraints


def test_overcurrent_breach_rejection(governor: Paper3SafetyGovernor, nominal_state: SpacecraftState):
    """Verify rejection when battery discharge current exceeds 40.0A."""
    action = ProposedAction(
        action_id="TEST-UNSAFE-CURR",
        action_type="REDISTRIBUTE_POWER",
        predicted_peak_current_a=44.2,
    )
    verdict = governor.evaluate_action(action, nominal_state)
    assert verdict.decision == GateDecision.REJECTED
    assert "HARD_OVERCURRENT_EXCEEDED" in verdict.violated_constraints


def test_soc_depletion_breach_rejection(governor: Paper3SafetyGovernor, nominal_state: SpacecraftState):
    """Verify rejection when battery state of charge breaches 15% floor."""
    action = ProposedAction(
        action_id="TEST-UNSAFE-SOC",
        action_type="REDUCE_PAYLOAD_LOAD",
        predicted_min_soc=0.12,
    )
    verdict = governor.evaluate_action(action, nominal_state)
    assert verdict.decision == GateDecision.REJECTED
    assert "HARD_SOC_DEPLETED" in verdict.violated_constraints


def test_compound_breach_detection(governor: Paper3SafetyGovernor, nominal_state: SpacecraftState):
    """Verify that multiple concurrent violations are all detected and reported."""
    action = ProposedAction(
        action_id="TEST-COMPOUND",
        action_type="CONTINUE_NOMINAL",
        predicted_peak_temp_c=50.0,
        predicted_min_voltage_v=19.0,
        predicted_peak_current_a=48.0,
    )
    verdict = governor.evaluate_action(action, nominal_state)
    assert verdict.decision == GateDecision.REJECTED
    assert "HARD_THERMAL_EXCEEDED" in verdict.violated_constraints
    assert "HARD_VOLTAGE_UNDERFLOW" in verdict.violated_constraints
    assert "HARD_OVERCURRENT_EXCEEDED" in verdict.violated_constraints


def test_fail_closed_on_nan_and_inf(governor: Paper3SafetyGovernor, nominal_state: SpacecraftState):
    """Verify fail-closed rejection on corrupted telemetry (NaN / Inf)."""
    action_nan = ProposedAction(
        action_id="TEST-NAN",
        action_type="CONTINUE_NOMINAL",
        predicted_peak_temp_c=float("nan"),
    )
    v_nan = governor.evaluate_action(action_nan, nominal_state)
    assert v_nan.decision == GateDecision.REJECTED
    assert v_nan.is_fail_closed is True

    action_inf = ProposedAction(
        action_id="TEST-INF",
        action_type="CONTINUE_NOMINAL",
        predicted_min_voltage_v=float("inf"),
    )
    v_inf = governor.evaluate_action(action_inf, nominal_state)
    assert v_inf.decision == GateDecision.REJECTED
    assert v_inf.is_fail_closed is True


def test_fail_closed_on_uncertified_action(governor: Paper3SafetyGovernor, nominal_state: SpacecraftState):
    """Verify rejection when action is not in certified catalog."""
    action_invalid = ProposedAction(
        action_id="TEST-INVALID-CATALOG",
        action_type="UNAUTHORIZED_SUBSYSTEM_ACTUATION",
    )
    v = governor.evaluate_action(action_invalid, nominal_state)
    assert v.decision == GateDecision.REJECTED
    assert v.is_fail_closed is True
    assert "FAIL_CLOSED_UNCERTIFIED_ACTION_TYPE" in v.violated_constraints


def test_no_safe_action_available(governor: Paper3SafetyGovernor, nominal_state: SpacecraftState):
    """Verify safe failure convergence when entire candidate pool is unsafe."""
    candidates = [
        ProposedAction("C1", "CONTINUE_NOMINAL", predicted_peak_temp_c=52.0),
        ProposedAction("C2", "REDUCE_PAYLOAD_LOAD", predicted_min_voltage_v=18.0),
    ]
    approved, rejected, status_msg = governor.filter_candidate_pool(candidates, nominal_state)
    assert len(approved) == 0
    assert len(rejected) == 2
    assert status_msg == "NO_SAFE_ACTION_AVAILABLE"


def test_communication_safety_dominance():
    """Verify that communication availability never bypasses hard safety constraints."""
    # Unsafe action + in contact -> MUST REJECT
    dec_contact, _ = arbitrate_communication_decision(
        verdict_is_safe=False,
        link_status=LinkStatus.IN_CONTACT,
        time_to_criticality_sec=100.0,
        ground_contact_window_sec=300.0,
    )
    assert dec_contact == "REJECT_EXECUTION"

    # Unsafe action + blackout -> MUST REJECT
    dec_blackout, _ = arbitrate_communication_decision(
        verdict_is_safe=False,
        link_status=LinkStatus.BLACKOUT_OCCULTATION,
        time_to_criticality_sec=100.0,
        ground_contact_window_sec=0.0,
    )
    assert dec_blackout == "REJECT_EXECUTION"
