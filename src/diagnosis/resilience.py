"""Unknown-failure resilience, out-of-distribution detection, and uncertainty-gated safe fallback."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from src.diagnosis.schema import DiagnosisReport, DiagnosisStatus, FailureMode
from src.planner.actions import RecoveryAction, RecoveryActionType
from src.planner.recovery_planner import ActionPlanReport


class ResilienceProfile(BaseModel):
    """Evaluation summary of system behavior on novel/unseen conditions."""
    scenario_name: str
    is_known_condition: bool
    diagnosis_status: DiagnosisStatus
    epistemic_uncertainty: float
    aleatoric_uncertainty: float
    confidence: float
    abstained_from_aggressive_action: bool
    safe_fallback_triggered: bool
    rationale: str


class UnknownFailureResilienceEvaluator:
    """Evaluates and enforces conservative safety gating when facing high-uncertainty / OOD anomalies."""

    def __init__(self, max_epistemic_for_aggressive_action: float = 0.50):
        self.max_epistemic_threshold = max_epistemic_for_aggressive_action

    def evaluate_gating(
        self,
        diagnosis: DiagnosisReport,
        proposed_plan: ActionPlanReport
    ) -> ResilienceProfile:
        """Enforce uncertainty-gated execution policies."""
        is_ood = (diagnosis.status == DiagnosisStatus.UNKNOWN_FAILURE or diagnosis.epistemic_uncertainty > self.max_epistemic_threshold)
        
        abstained = False
        fallback = False
        rationale = ""

        if is_ood:
            # Epistemic uncertainty is high (Out-Of-Distribution)
            abstained = True
            # Inhibit aggressive actions (e.g. irreversible power bus cutouts)
            # Default to conservative reversible standby/safe mode
            fallback = True
            rationale = (
                f"High epistemic uncertainty ({diagnosis.epistemic_uncertainty:.3f} > {self.max_epistemic_threshold:.2f}). "
                "Aggressive autonomous action INHIBITED. Reversible safe standby commanded while queuing full diagnostic frame for ground inspection."
            )
        else:
            abstained = False
            fallback = False
            rationale = (
                f"Low epistemic uncertainty ({diagnosis.epistemic_uncertainty:.3f} <= {self.max_epistemic_threshold:.2f}). "
                f"Fault conforms to known {diagnosis.primary_failure_mode} manifold. Autonomous recovery plan authorized."
            )

        return ResilienceProfile(
            scenario_name=diagnosis.primary_failure_mode,
            is_known_condition=not is_ood,
            diagnosis_status=diagnosis.status,
            epistemic_uncertainty=diagnosis.epistemic_uncertainty,
            aleatoric_uncertainty=diagnosis.aleatoric_uncertainty,
            confidence=diagnosis.confidence,
            abstained_from_aggressive_action=abstained,
            safe_fallback_triggered=fallback,
            rationale=rationale
        )
