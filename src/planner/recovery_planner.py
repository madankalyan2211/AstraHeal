"""Autonomous Recovery Planner combining counterfactual simulation and deterministic safety gating."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from pydantic import BaseModel, Field

from src.diagnosis.schema import DiagnosisReport
from src.digital_twin.simulator import SpacecraftEPSDigitalTwin
from src.planner.actions import RecoveryAction, ActionGenerator
from src.planner.counterfactual import CounterfactualSimulator
from src.planner.scenario import ScenarioResult
from src.safety.safety_governor import DeterministicSafetyGovernor, SafetyDecision, SafetyStatus


class ActionPlanReport(BaseModel):
    """Auditable final plan selected by the autonomous recovery planner."""
    timestamp: float
    diagnosis: str
    confidence: float
    total_candidates_evaluated: int
    approved_candidates_count: int
    rejected_candidates_count: int
    selected_action: Optional[RecoveryAction] = Field(default=None)
    selection_score: float
    safety_decision: Optional[SafetyDecision] = Field(default=None)
    all_evaluated_scenarios: List[Dict[str, Any]] = Field(default_factory=list)
    decision_rationale: List[str] = Field(default_factory=list)


class AutonomousRecoveryPlanner:
    """Multi-objective autonomous recovery planner gated by the Deterministic Safety Governor."""

    def __init__(
        self,
        governor: Optional[DeterministicSafetyGovernor] = None,
        simulator: Optional[CounterfactualSimulator] = None,
        weights: Optional[Dict[str, float]] = None
    ):
        self.governor = governor or DeterministicSafetyGovernor()
        self.simulator = simulator or CounterfactualSimulator()
        
        # Multi-objective soft ranking weights
        self.weights = weights or {
            "survival": 0.40,
            "payload_utility": 0.25,
            "energy_margin": 0.15,
            "reversibility": 0.10,
            "disruption_penalty": 0.10
        }
        total_w = sum(self.weights.values())
        self.weights = {k: v / total_w for k, v in self.weights.items()}

    def score_scenario(self, scenario: ScenarioResult, decision: SafetyDecision) -> float:
        """Compute transparent multi-objective score for an approved candidate scenario."""
        if not decision.is_safe:
            return -1e9  # Strictly disqualified

        # 1. Survival & Thermal/Voltage Safety Margin Score [0, 1]
        t_margin = max(0.0, min(20.0, decision.safety_margins.get("thermal_margin_c", 0.0))) / 20.0
        v_margin = max(0.0, min(8.0, decision.safety_margins.get("voltage_margin_v", 0.0))) / 8.0
        survival_score = 0.5 * t_margin + 0.5 * v_margin

        # 2. Payload capability preserved [0, 1]
        payload_score = scenario.mission_impact.payload_availability_fraction

        # 3. Energy margin score [0, 1] (normalized against 500 Wh reference)
        energy_score = max(0.0, min(1.0, scenario.mission_impact.energy_margin_wh / 500.0))

        # 4. Reversibility score [0, 1]
        rev_score = scenario.mission_impact.reversibility_score

        # 5. Disruption penalty [0, 1] (lower cost is better)
        disruption_penalty = scenario.mission_impact.disruption_penalty

        # Weighted combination
        total_score = (
            self.weights["survival"] * survival_score
            + self.weights["payload_utility"] * payload_score
            + self.weights["energy_margin"] * energy_score
            + self.weights["reversibility"] * rev_score
            - self.weights["disruption_penalty"] * disruption_penalty
        )
        return float(total_score)

    def plan_recovery(
        self,
        twin: SpacecraftEPSDigitalTwin,
        diagnosis: DiagnosisReport,
        horizon_sec: Optional[float] = None
    ) -> ActionPlanReport:
        """Execute end-to-end autonomous recovery planning pipeline."""
        t = twin.current_time_sec

        # 1. Generate domain-tailored candidate actions
        candidates = ActionGenerator.generate_candidates(diagnosis, twin)

        # 2. Simulate candidates forward in isolated digital twin branches
        scenarios = self.simulator.evaluate_all(twin, candidates, horizon_sec=horizon_sec)

        # 3. Filter scenarios through the Deterministic Safety Governor
        approved_pairs, rejected_pairs = self.governor.filter_safe_scenarios(scenarios)

        evaluated_records = []
        for scen in scenarios:
            dec = self.governor.evaluate(scen)
            sc = self.score_scenario(scen, dec)
            evaluated_records.append({
                "action_id": scen.action.action_id,
                "action_type": scen.action.action_type.value,
                "description": scen.action.description,
                "safety_status": dec.status.value,
                "score": sc,
                "max_temp_c": scen.risk_metrics.max_battery_temp_c,
                "min_voltage_v": scen.risk_metrics.min_bus_voltage_v,
                "min_soc": scen.risk_metrics.min_state_of_charge,
                "payload_fraction": scen.mission_impact.payload_availability_fraction,
                "violations": dec.rejection_reasons
            })

        # 4. Rank approved candidates
        ranked_approved = []
        for scen, dec in approved_pairs:
            sc = self.score_scenario(scen, dec)
            ranked_approved.append((scen, dec, sc))

        ranked_approved.sort(key=lambda x: x[2], reverse=True)

        # 5. Select optimal safe action
        rationale = []
        if ranked_approved:
            best_scen, best_dec, best_score = ranked_approved[0]
            selected_action = best_scen.action
            rationale.append(
                f"Selected {selected_action.action_id} ({selected_action.action_type.value}) with optimal safety-utility score ({best_score:.3f})."
            )
            rationale.append(
                f"Preserves {best_scen.mission_impact.payload_availability_fraction*100:.0f}% payload capability while maintaining {best_dec.safety_margins.get('thermal_margin_c', 0.0):.1f}°C thermal margin."
            )
            for _, dec, _ in ranked_approved[1:]:
                rationale.append(f"Passed safety but ranked lower than optimal candidate: {dec.action_id}")
        else:
            # Fallback emergency safe mode if no candidate passed hard constraints
            selected_action = next((c for c in candidates if c.action_id == "ACT-01-SAFE-MODE"), None)
            best_score = -1.0
            best_dec = self.governor.evaluate(scenarios[0]) if scenarios else None
            rationale.append("CRITICAL: No evaluated scenario fully satisfied all hard constraints. Triggering Emergency Safe Mode.")

        if rejected_pairs:
            for scen, dec in rejected_pairs:
                rationale.append(f"Disqualified {dec.action_id}: {'; '.join(dec.rejection_reasons)}")

        return ActionPlanReport(
            timestamp=t,
            diagnosis=diagnosis.primary_failure_mode,
            confidence=diagnosis.confidence,
            total_candidates_evaluated=len(scenarios),
            approved_candidates_count=len(approved_pairs),
            rejected_candidates_count=len(rejected_pairs),
            selected_action=selected_action,
            selection_score=best_score,
            safety_decision=best_dec,
            all_evaluated_scenarios=evaluated_records,
            decision_rationale=rationale
        )

    def execute_plan_on_twin(self, twin: SpacecraftEPSDigitalTwin, plan: ActionPlanReport) -> bool:
        """Apply the approved plan action directly to the active spacecraft digital twin."""
        if plan.selected_action is None:
            return False

        # Safety Governor Final Pre-Execution Gate
        # Re-verify that the action is not marked REJECTED
        if plan.safety_decision and plan.safety_decision.status == SafetyStatus.REJECTED and plan.approved_candidates_count > 0:
            raise RuntimeError(f"Safety Governor Violation: Cannot execute REJECTED action {plan.selected_action.action_id}")

        plan.selected_action.apply_to_digital_twin(twin)
        return True
