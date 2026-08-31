"""Counterfactual scenario evaluation schemas, risk metrics, and mission impact models."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd
from pydantic import BaseModel, Field

from src.planner.actions import RecoveryAction


class RiskMetrics(BaseModel):
    """Predicted safety and physical risk indicators over the simulation horizon."""
    max_battery_temp_c: float
    min_bus_voltage_v: float
    max_battery_current_a: float
    min_state_of_charge: float
    final_state_of_charge: float
    cumulative_joule_heat_kj: float
    thermal_runaway_triggered: bool = False
    voltage_collapse_triggered: bool = False


class MissionImpact(BaseModel):
    """Predicted mission capability and utility outcomes."""
    payload_availability_fraction: float = Field(..., ge=0.0, le=1.0)
    energy_margin_wh: float
    battery_degradation_delta_soh: float
    reversibility_score: float = Field(..., ge=0.0, le=1.0)
    disruption_penalty: float = Field(..., ge=0.0, le=1.0)


class ScenarioResult(BaseModel):
    """Structured evaluation output of a single counterfactual branch."""
    action: RecoveryAction
    simulation_seed: int
    duration_sec: float
    survived: bool
    risk_metrics: RiskMetrics
    mission_impact: MissionImpact
    constraint_violations: List[str] = Field(default_factory=list)
    initial_snapshot: Dict[str, Any] = Field(default_factory=dict)
    predicted_final_snapshot: Dict[str, Any] = Field(default_factory=dict)
    status: str = "COMPLETED"
    trajectory_summary: Dict[str, float] = Field(default_factory=dict)
