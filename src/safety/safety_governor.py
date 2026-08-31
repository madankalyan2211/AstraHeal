"""Deterministic Safety Governor for autonomous spacecraft command authorization."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.planner.scenario import ScenarioResult


class SafetyStatus(str, Enum):
    """Safety authorization status."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class SafetyConstraint(BaseModel):
    """Specification of a deterministic physical or operational hard safety constraint."""
    name: str
    description: str
    threshold_value: float
    comparison: str  # "MAX", "MIN", "EQUAL"
    is_critical: bool = True


class SafetyDecision(BaseModel):
    """Deterministic authorization verdict produced by the Safety Governor."""
    action_id: str
    status: SafetyStatus
    is_safe: bool
    violated_hard_constraints: List[str] = Field(default_factory=list)
    rejection_reasons: List[str] = Field(default_factory=list)
    safety_margins: Dict[str, float] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeterministicSafetyGovernor:
    """The authoritative gatekeeper enforcing hard physical constraints on all proposed recovery actions.
    
    CRITICAL ARCHITECTURAL INVARIANT:
    No AI, planner, or agent can execute actions directly on the spacecraft simulation without
    prior evaluation and explicit deterministic approval from this governor.
    """

    DEFAULT_HARD_CONSTRAINTS = {
        "max_battery_temp_c": 46.0,         # Exothermic runaway barrier
        "min_bus_voltage_v": 22.0,          # Undervoltage lockout threshold
        "max_battery_current_a": 40.0,      # Overcurrent protection limit
        "min_battery_soc": 0.15,            # Permanent cell damage floor (15% reserve)
        "require_survival": True,           # Spacecraft must not enter irrecoverable collapse
    }

    def __init__(self, constraints: Optional[Dict[str, Any]] = None):
        self.constraints = constraints or self.DEFAULT_HARD_CONSTRAINTS.copy()

    def evaluate(self, scenario: ScenarioResult) -> SafetyDecision:
        """Evaluate predicted counterfactual trajectory against immutable hard safety invariants."""
        action_id = scenario.action.action_id
        risk = scenario.risk_metrics
        viols: List[str] = []
        reasons: List[str] = []
        margins: Dict[str, float] = {}

        # 1. Thermal Hard Constraint: Battery Core Temperature
        max_temp_limit = float(self.constraints["max_battery_temp_c"])
        temp_margin = max_temp_limit - risk.max_battery_temp_c
        margins["thermal_margin_c"] = float(temp_margin)
        if risk.max_battery_temp_c > max_temp_limit:
            viols.append("HARD_THERMAL_EXCEEDED")
            reasons.append(
                f"Predicted peak battery temperature ({risk.max_battery_temp_c:.1f}°C) exceeds hard safety threshold ({max_temp_limit:.1f}°C)."
            )

        # 2. Voltage Hard Constraint: Bus Undervoltage Lockout
        min_v_limit = float(self.constraints["min_bus_voltage_v"])
        volt_margin = risk.min_bus_voltage_v - min_v_limit
        margins["voltage_margin_v"] = float(volt_margin)
        if risk.min_bus_voltage_v < min_v_limit:
            viols.append("HARD_VOLTAGE_UNDERFLOW")
            reasons.append(
                f"Predicted minimum bus voltage ({risk.min_bus_voltage_v:.1f}V) collapses below essential operational floor ({min_v_limit:.1f}V)."
            )

        # 3. Overcurrent Hard Constraint
        max_i_limit = float(self.constraints["max_battery_current_a"])
        curr_margin = max_i_limit - risk.max_battery_current_a
        margins["current_margin_a"] = float(curr_margin)
        if risk.max_battery_current_a > max_i_limit:
            viols.append("HARD_OVERCURRENT_EXCEEDED")
            reasons.append(
                f"Predicted peak battery current ({risk.max_battery_current_a:.1f}A) exceeds PDU safety rating ({max_i_limit:.1f}A)."
            )

        # 4. State of Charge Hard Floor
        min_soc_limit = float(self.constraints["min_battery_soc"])
        soc_margin = risk.min_state_of_charge - min_soc_limit
        margins["soc_margin_pct"] = float(soc_margin * 100.0)
        if risk.min_state_of_charge < min_soc_limit:
            viols.append("HARD_SOC_DEPLETED")
            reasons.append(
                f"Predicted minimum SoC ({risk.min_state_of_charge*100:.1f}%) breaches critical battery reserve floor ({min_soc_limit*100:.1f}%)."
            )

        # 5. Survival Outcome Hard Invariant
        if not scenario.survived:
            viols.append("HARD_SURVIVAL_FAILED")
            reasons.append("Counterfactual branch predicted fatal spacecraft collapse or unrecoverable power loss.")

        # Verdict
        is_safe = (len(viols) == 0)
        status = SafetyStatus.APPROVED if is_safe else SafetyStatus.REJECTED

        return SafetyDecision(
            action_id=action_id,
            status=status,
            is_safe=is_safe,
            violated_hard_constraints=viols,
            rejection_reasons=reasons,
            safety_margins=margins,
            metadata={"action_type": scenario.action.action_type.value, "sim_seed": scenario.simulation_seed}
        )

    def filter_safe_scenarios(
        self,
        scenarios: List[ScenarioResult]
    ) -> Tuple[List[Tuple[ScenarioResult, SafetyDecision]], List[Tuple[ScenarioResult, SafetyDecision]]]:
        """Separate candidate scenarios into approved vs rejected lists with explicit rationale."""
        approved = []
        rejected = []

        for scen in scenarios:
            dec = self.evaluate(scen)
            if dec.is_safe:
                approved.append((scen, dec))
            else:
                rejected.append((scen, dec))

        return approved, rejected
