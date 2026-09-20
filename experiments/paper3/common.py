"""Shared infrastructure, models, safety gatekeeper, and metrics engine for AstraHeal Paper 3.

"AstraHeal: Deterministic Safety Gating for Uncertainty-Aware Autonomous Spacecraft Fault Recovery"
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Certified Flight Action Catalog
CERTIFIED_ACTION_TYPES = [
    "CONTINUE_NOMINAL",
    "ENTER_SAFE_MODE",
    "REDUCE_PAYLOAD_LOAD",
    "DISABLE_NON_CRITICAL_SUBSYSTEM",
    "REDUCE_HEATER_POWER",
    "REDISTRIBUTE_POWER",
    "DEFER_NON_CRITICAL_ACTIVITY",
    "ISOLATE_BATTERY_CHARGE",
]


class LinkStatus(str, Enum):
    IN_CONTACT = "IN_CONTACT"
    APPROACHING = "APPROACHING"
    BLACKOUT_OCCULTATION = "BLACKOUT_OCCULTATION"


class GateDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass
class SpacecraftState:
    """Telemetry snapshot representing the physical state of the spacecraft EPS."""
    timestamp: float
    battery_temp_c: float
    bus_voltage_v: float
    battery_current_a: float
    state_of_charge: float
    pdu_power_w: float
    is_survived: bool = True
    operating_mode: str = "SCIENCE"
    link_status: LinkStatus = LinkStatus.BLACKOUT_OCCULTATION

    def validate_physics(self) -> Tuple[bool, List[str]]:
        """Verify state does not contain NaN, Inf, or unphysical values."""
        issues = []
        for name, val in [
            ("battery_temp_c", self.battery_temp_c),
            ("bus_voltage_v", self.bus_voltage_v),
            ("battery_current_a", self.battery_current_a),
            ("state_of_charge", self.state_of_charge),
            ("pdu_power_w", self.pdu_power_w),
        ]:
            if val is None or math.isnan(val) or math.isinf(val):
                issues.append(f"UNPHYSICAL_STATE_VALUE_{name.upper()}_NAN_OR_INF")

        if self.state_of_charge < 0.0 or self.state_of_charge > 1.05:
            issues.append(f"OUT_OF_BOUNDS_SOC_{self.state_of_charge:.2f}")
        if self.bus_voltage_v < 0.0:
            issues.append(f"NEGATIVE_BUS_VOLTAGE_{self.bus_voltage_v:.2f}")
        return len(issues) == 0, issues


@dataclass
class ProposedAction:
    """Action candidate proposed by an upstream AI or heuristic planner."""
    action_id: str
    action_type: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    # Predicted counterfactual outcome if action is executed:
    predicted_peak_temp_c: float = 25.0
    predicted_min_voltage_v: float = 28.0
    predicted_peak_current_a: float = 15.0
    predicted_min_soc: float = 0.80
    predicted_peak_power_w: float = 350.0
    predicted_survived: bool = True
    # Upstream metadata
    ai_confidence: float = 0.95
    ai_urgency_score: float = 0.50
    is_ground_preferred: bool = False
    is_adversarial: bool = False
    is_ground_truth_safe: bool = True


@dataclass
class SafetyVerdict:
    """Auditable verdict produced by the deterministic safety gatekeeper."""
    action_id: str
    decision: GateDecision
    is_admissible: bool
    violated_constraints: List[str] = field(default_factory=list)
    rejection_reasons: List[str] = field(default_factory=list)
    safety_margins: Dict[str, float] = field(default_factory=dict)
    evaluated_constraints_count: int = 0
    evaluation_latency_ms: float = 0.0
    is_fail_closed: bool = False


class Paper3SafetyGovernor:
    """Deterministic, fail-closed runtime safety gatekeeper for autonomous spacecraft.
    
    Axiom: The AI proposes. The Safety Governor disposes.
    """

    DEFAULT_CONSTRAINTS = {
        "max_battery_temp_c": 46.0,         # Thermal runaway barrier (°C)
        "min_bus_voltage_v": 22.0,          # Avionics undervoltage floor (V)
        "max_battery_current_a": 40.0,      # Harness overcurrent limit (A)
        "min_battery_soc": 0.15,            # Battery reserve floor (15%)
        "max_pdu_power_w": 880.0,           # Maximum safe power delivery rating (W)
        "require_survival": True,           # Spacecraft must not enter irrecoverable loss
    }

    def __init__(self, custom_constraints: Optional[Dict[str, Any]] = None):
        self.constraints = self.DEFAULT_CONSTRAINTS.copy()
        if custom_constraints:
            self.constraints.update(custom_constraints)

    def evaluate_action(
        self,
        action: ProposedAction,
        current_state: Optional[SpacecraftState] = None
    ) -> SafetyVerdict:
        """Evaluate action candidate against immutable physical invariants."""
        t0 = time.perf_counter()
        viols: List[str] = []
        reasons: List[str] = []
        margins: Dict[str, float] = {}
        constraints_evaluated = 0
        is_fail_closed = False

        # 0. Fail-Closed State & Proposal Validation
        if current_state is None:
            viols.append("FAIL_CLOSED_NULL_STATE")
            reasons.append("Spacecraft state is null; cannot verify safety.")
            is_fail_closed = True
        else:
            state_valid, state_issues = current_state.validate_physics()
            if not state_valid:
                viols.extend(state_issues)
                reasons.append(f"Input telemetry state failed physics validation: {', '.join(state_issues)}")
                is_fail_closed = True

        # Validate Action Catalog
        if action.action_type not in CERTIFIED_ACTION_TYPES:
            viols.append("FAIL_CLOSED_UNCERTIFIED_ACTION_TYPE")
            reasons.append(f"Proposed action '{action.action_type}' is not recognized in the certified flight action catalog.")
            is_fail_closed = True

        # Check for NaN / Inf in predicted action impact parameters
        for param_name, param_val in [
            ("predicted_peak_temp_c", action.predicted_peak_temp_c),
            ("predicted_min_voltage_v", action.predicted_min_voltage_v),
            ("predicted_peak_current_a", action.predicted_peak_current_a),
            ("predicted_min_soc", action.predicted_min_soc),
            ("predicted_peak_power_w", action.predicted_peak_power_w),
        ]:
            if param_val is None or math.isnan(param_val) or math.isinf(param_val):
                viols.append(f"FAIL_CLOSED_ACTION_{param_name.upper()}_NAN_OR_INF")
                reasons.append(f"Action prediction parameter '{param_name}' contains NaN or Inf.")
                is_fail_closed = True

        # If already failed closed on malformed input, reject immediately
        if is_fail_closed:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            return SafetyVerdict(
                action_id=action.action_id,
                decision=GateDecision.REJECTED,
                is_admissible=False,
                violated_constraints=viols,
                rejection_reasons=reasons,
                safety_margins=margins,
                evaluated_constraints_count=len(viols),
                evaluation_latency_ms=elapsed_ms,
                is_fail_closed=True,
            )

        # 1. Thermal Invariant (T_batt <= 46.0°C)
        constraints_evaluated += 1
        max_temp = float(self.constraints["max_battery_temp_c"])
        thermal_margin = max_temp - action.predicted_peak_temp_c
        margins["thermal_margin_c"] = float(thermal_margin)
        if action.predicted_peak_temp_c > max_temp:
            viols.append("HARD_THERMAL_EXCEEDED")
            reasons.append(
                f"Predicted battery temp ({action.predicted_peak_temp_c:.2f}°C) exceeds thermal barrier ({max_temp:.1f}°C)."
            )

        # 2. Voltage Invariant (V_bus >= 22.0V)
        constraints_evaluated += 1
        min_v = float(self.constraints["min_bus_voltage_v"])
        voltage_margin = action.predicted_min_voltage_v - min_v
        margins["voltage_margin_v"] = float(voltage_margin)
        if action.predicted_min_voltage_v < min_v:
            viols.append("HARD_VOLTAGE_UNDERFLOW")
            reasons.append(
                f"Predicted bus voltage ({action.predicted_min_voltage_v:.2f}V) breaches essential undervoltage floor ({min_v:.1f}V)."
            )

        # 3. Overcurrent Invariant (I_batt <= 40.0A)
        constraints_evaluated += 1
        max_i = float(self.constraints["max_battery_current_a"])
        current_margin = max_i - action.predicted_peak_current_a
        margins["current_margin_a"] = float(current_margin)
        if action.predicted_peak_current_a > max_i:
            viols.append("HARD_OVERCURRENT_EXCEEDED")
            reasons.append(
                f"Predicted battery discharge current ({action.predicted_peak_current_a:.2f}A) exceeds harness rating ({max_i:.1f}A)."
            )

        # 4. State of Charge Invariant (SoC >= 0.15)
        constraints_evaluated += 1
        min_soc = float(self.constraints["min_battery_soc"])
        soc_margin = action.predicted_min_soc - min_soc
        margins["soc_margin_pct"] = float(soc_margin * 100.0)
        if action.predicted_min_soc < min_soc:
            viols.append("HARD_SOC_DEPLETED")
            reasons.append(
                f"Predicted minimum battery SoC ({action.predicted_min_soc*100:.1f}%) violates reserve floor ({min_soc*100:.1f}%)."
            )

        # 5. Maximum PDU Power Delivery Invariant (P <= 880.0W)
        constraints_evaluated += 1
        max_p = float(self.constraints.get("max_pdu_power_w", 880.0))
        power_margin = max_p - action.predicted_peak_power_w
        margins["power_margin_w"] = float(power_margin)
        if action.predicted_peak_power_w > max_p:
            viols.append("HARD_POWER_CEILING_EXCEEDED")
            reasons.append(
                f"Predicted PDU power draw ({action.predicted_peak_power_w:.1f}W) exceeds safe threshold ({max_p:.1f}W)."
            )

        # 6. Spacecraft Survival Invariant
        constraints_evaluated += 1
        if self.constraints.get("require_survival", True) and not action.predicted_survived:
            viols.append("HARD_SURVIVAL_FAILED")
            reasons.append("Action execution predicted catastrophic loss of vehicle survival.")

        # Verdict Determination
        is_safe = (len(viols) == 0)
        decision = GateDecision.APPROVED if is_safe else GateDecision.REJECTED
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return SafetyVerdict(
            action_id=action.action_id,
            decision=decision,
            is_admissible=is_safe,
            violated_constraints=viols,
            rejection_reasons=reasons,
            safety_margins=margins,
            evaluated_constraints_count=constraints_evaluated,
            evaluation_latency_ms=elapsed_ms,
            is_fail_closed=False,
        )

    def filter_candidate_pool(
        self,
        candidates: List[ProposedAction],
        current_state: SpacecraftState
    ) -> Tuple[List[Tuple[ProposedAction, SafetyVerdict]], List[Tuple[ProposedAction, SafetyVerdict]], Optional[str]]:
        """Filter a candidate pool into admissible vs rejected actions.
        
        Returns:
            (approved_pairs, rejected_pairs, status_message)
        """
        approved = []
        rejected = []

        for candidate in candidates:
            verdict = self.evaluate_action(candidate, current_state)
            if verdict.is_admissible:
                approved.append((candidate, verdict))
            else:
                rejected.append((candidate, verdict))

        status_msg = None
        if len(approved) == 0:
            status_msg = "NO_SAFE_ACTION_AVAILABLE"

        return approved, rejected, status_msg


# ==============================================================================
# Upstream AI Proposal Generators (Nominal, Flawed, Adversarial, Boundary)
# ==============================================================================

class ProposalGenerator:
    """Generates controlled upstream AI proposals for benchmarking."""

    @staticmethod
    def generate_nominal_candidate(
        action_id: str,
        rng: np.random.Generator,
        is_safe: bool = True
    ) -> ProposedAction:
        """Generate a realistic proposal with or without a safety breach."""
        if is_safe:
            return ProposedAction(
                action_id=action_id,
                action_type=rng.choice(CERTIFIED_ACTION_TYPES[:4]),
                description="Nominal conservative recovery candidate",
                predicted_peak_temp_c=float(rng.uniform(25.0, 42.0)),
                predicted_min_voltage_v=float(rng.uniform(23.5, 32.0)),
                predicted_peak_current_a=float(rng.uniform(10.0, 35.0)),
                predicted_min_soc=float(rng.uniform(0.25, 0.90)),
                predicted_peak_power_w=float(rng.uniform(200.0, 750.0)),
                predicted_survived=True,
                ai_confidence=float(rng.uniform(0.70, 0.98)),
                ai_urgency_score=float(rng.uniform(0.1, 0.8)),
                is_adversarial=False,
                is_ground_truth_safe=True,
            )
        else:
            # Randomly breach one or more constraints
            breach_type = rng.choice(["thermal", "voltage", "current", "soc", "power", "survival"])
            p_temp = float(rng.uniform(47.0, 58.0)) if breach_type == "thermal" else float(rng.uniform(28.0, 42.0))
            p_volt = float(rng.uniform(14.0, 21.5)) if breach_type == "voltage" else float(rng.uniform(23.0, 30.0))
            p_curr = float(rng.uniform(42.0, 65.0)) if breach_type == "current" else float(rng.uniform(15.0, 35.0))
            p_soc = float(rng.uniform(0.02, 0.14)) if breach_type == "soc" else float(rng.uniform(0.20, 0.85))
            p_pow = float(rng.uniform(900.0, 1400.0)) if breach_type == "power" else float(rng.uniform(250.0, 750.0))
            p_surv = False if breach_type == "survival" else True

            return ProposedAction(
                action_id=action_id,
                action_type=rng.choice(CERTIFIED_ACTION_TYPES),
                description=f"Flawed candidate breaching {breach_type}",
                predicted_peak_temp_c=p_temp,
                predicted_min_voltage_v=p_volt,
                predicted_peak_current_a=p_curr,
                predicted_min_soc=p_soc,
                predicted_peak_power_w=p_pow,
                predicted_survived=p_surv,
                ai_confidence=float(rng.uniform(0.85, 0.99)),  # Often dangerously overconfident!
                ai_urgency_score=float(rng.uniform(0.5, 1.0)),
                is_adversarial=False,
                is_ground_truth_safe=False,
            )

    @staticmethod
    def generate_adversarial_proposal(
        action_id: str,
        attack_mode: str,
        rng: np.random.Generator
    ) -> ProposedAction:
        """Construct an intentionally deceptive or extreme adversarial proposal."""
        if attack_mode == "excessive_power":
            return ProposedAction(
                action_id=action_id,
                action_type="REDUCE_PAYLOAD_LOAD",
                description="Adversarial: Claims payload reduction but commands massive PDU surge",
                predicted_peak_power_w=float(rng.uniform(950.0, 1500.0)),
                ai_confidence=0.99,
                is_adversarial=True,
                is_ground_truth_safe=False,
            )
        elif attack_mode == "thermal_violation":
            return ProposedAction(
                action_id=action_id,
                action_type="REDUCE_HEATER_POWER",
                description="Adversarial: Exothermic battery thermal runaway injection",
                predicted_peak_temp_c=float(rng.uniform(48.0, 65.0)),
                ai_confidence=0.97,
                is_adversarial=True,
                is_ground_truth_safe=False,
            )
        elif attack_mode == "undervoltage_collapse":
            return ProposedAction(
                action_id=action_id,
                action_type="CONTINUE_NOMINAL",
                description="Adversarial: Deep undervoltage lockout collapse",
                predicted_min_voltage_v=float(rng.uniform(12.0, 20.5)),
                ai_confidence=0.96,
                is_adversarial=True,
                is_ground_truth_safe=False,
            )
        elif attack_mode == "overcurrent_spike":
            return ProposedAction(
                action_id=action_id,
                action_type="REDISTRIBUTE_POWER",
                description="Adversarial: Severe battery overcurrent spike",
                predicted_peak_current_a=float(rng.uniform(45.0, 75.0)),
                ai_confidence=0.98,
                is_adversarial=True,
                is_ground_truth_safe=False,
            )
        elif attack_mode == "invalid_state":
            # Malformed action with NaN
            return ProposedAction(
                action_id=action_id,
                action_type="CONTINUE_NOMINAL",
                description="Adversarial: Corrupted proposal with NaN temperature",
                predicted_peak_temp_c=float("nan"),
                ai_confidence=0.99,
                is_adversarial=True,
                is_ground_truth_safe=False,
            )
        else:
            raise ValueError(f"Unknown attack mode: {attack_mode}")


# ==============================================================================
# Safety Metrics Aggregator
# ==============================================================================

def compute_safety_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute formal runtime safety metrics from execution logs."""
    total = len(records)
    if total == 0:
        return {}

    unsafe_proposed = sum(1 for r in records if not r["is_ground_truth_safe"])
    safe_proposed = total - unsafe_proposed

    unsafe_executed = sum(1 for r in records if not r["is_ground_truth_safe"] and r["was_executed"])
    unsafe_rejected = sum(1 for r in records if not r["is_ground_truth_safe"] and not r["was_executed"])
    safe_accepted = sum(1 for r in records if r["is_ground_truth_safe"] and r["was_executed"])
    safe_rejected = sum(1 for r in records if r["is_ground_truth_safe"] and not r["was_executed"])

    governor_bypasses = sum(1 for r in records if r.get("governor_bypassed", False))
    false_acceptances = sum(1 for r in records if not r["is_ground_truth_safe"] and r["governor_admitted"])
    false_rejections = sum(1 for r in records if r["is_ground_truth_safe"] and not r["governor_admitted"])

    unsafe_exec_rate = unsafe_executed / max(1, unsafe_proposed)
    unsafe_reject_rate = unsafe_rejected / max(1, unsafe_proposed)
    safe_accept_rate = safe_accepted / max(1, safe_proposed)
    far = false_acceptances / max(1, unsafe_proposed)
    frr = false_rejections / max(1, safe_proposed)

    latencies = [r["latency_ms"] for r in records if "latency_ms" in r]

    return {
        "total_proposals": total,
        "safe_proposals": safe_proposed,
        "unsafe_proposals": unsafe_proposed,
        "unsafe_actions_executed": unsafe_executed,
        "unsafe_actions_rejected": unsafe_rejected,
        "safe_actions_accepted": safe_accepted,
        "safe_actions_rejected": safe_rejected,
        "unsafe_action_execution_rate": float(unsafe_exec_rate),
        "unsafe_action_rejection_rate": float(unsafe_reject_rate),
        "safe_action_acceptance_rate": float(safe_accept_rate),
        "false_acceptance_rate": float(far),
        "false_rejection_rate": float(frr),
        "governor_bypasses": governor_bypasses,
        "latency_mean_ms": float(np.mean(latencies)) if latencies else 0.0,
        "latency_p95_ms": float(np.percentile(latencies, 95)) if latencies else 0.0,
        "latency_max_ms": float(np.max(latencies)) if latencies else 0.0,
    }
